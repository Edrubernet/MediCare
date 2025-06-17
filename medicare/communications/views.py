from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.http import JsonResponse
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import ChatRoom, ChatMessage
from .serializers import ChatRoomSerializer, ChatRoomListSerializer, ChatMessageSerializer
from staff.models import User

# Create your views here.

class IsParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.participants.filter(id=request.user.id).exists()


class ChatRoomViewSet(viewsets.ModelViewSet):
    """
    API endpoint for chat rooms.
    """
    queryset = ChatRoom.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsParticipant]

    def get_serializer_class(self):
        if self.action == 'list':
            return ChatRoomListSerializer
        return ChatRoomSerializer

    def get_queryset(self):
        # Return only chat rooms the user is a participant of
        return self.request.user.chat_rooms.all().prefetch_related('participants', 'messages__sender')

    @action(detail=False, methods=['post'])
    def create_or_get_room(self, request):
        """
        Create a new chat room between the request user and another user,
        or return the existing one if it already exists.
        """
        other_user_id = request.data.get('user_id')
        if not other_user_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        
        # Find a room with exactly these two participants
        # This is a simplified approach. A more robust solution might use a custom manager method.
        user_rooms = set(user.chat_rooms.values_list('id', flat=True))
        other_user_rooms = set(other_user.chat_rooms.values_list('id', flat=True))
        
        common_room_ids = user_rooms.intersection(other_user_rooms)
        
        for room_id in common_room_ids:
            room = ChatRoom.objects.get(id=room_id)
            if room.participants.count() == 2:
                serializer = ChatRoomSerializer(room)
                return Response(serializer.data, status=status.HTTP_200_OK)

        # If no such room exists, create a new one
        new_room = ChatRoom.objects.create(
            name=f"Chat between {user.username} and {other_user.username}"
        )
        new_room.participants.add(user, other_user)
        
        serializer = ChatRoomSerializer(new_room)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for chat messages.
    """
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only messages from rooms the user is a participant of
        user_room_ids = self.request.user.chat_rooms.values_list('id', flat=True)
        return self.queryset.filter(room_id__in=user_room_ids).select_related('sender', 'room')

    def perform_create(self, serializer):
        # Ensure the user can only send messages to rooms they're a participant of
        room = serializer.validated_data['room']
        if not room.participants.filter(id=self.request.user.id).exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You are not a participant of this room.")
        
        serializer.save(sender=self.request.user)

    @action(detail=False, methods=['get'])
    def room_messages(self, request):
        """
        Get messages for a specific room.
        """
        room_id = request.query_params.get('room_id')
        if not room_id:
            return Response({"error": "room_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return Response({"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if user is a participant
        if not room.participants.filter(id=request.user.id).exists():
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        messages = self.queryset.filter(room=room).order_by('timestamp')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)


# Web Views (Class-Based Views for chat management)
class ChatDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'communications/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['chat_rooms'] = user.chat_rooms.all().prefetch_related('participants')[:10]
        context['recent_messages'] = ChatMessage.objects.filter(
            room__participants=user
        ).order_by('-timestamp')[:5]
        return context


class ChatRoomListView(LoginRequiredMixin, ListView):
    model = ChatRoom
    template_name = 'communications/room_list.html'
    context_object_name = 'rooms'
    paginate_by = 10

    def get_queryset(self):
        return self.request.user.chat_rooms.all().prefetch_related('participants')


class ChatRoomCreateView(LoginRequiredMixin, CreateView):
    model = ChatRoom
    template_name = 'communications/room_create.html'
    fields = ['name']
    success_url = reverse_lazy('communications:chat_room_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Add the creator as a participant
        self.object.participants.add(self.request.user)
        return response


class ChatRoomDetailView(LoginRequiredMixin, DetailView):
    model = ChatRoom
    template_name = 'communications/room_detail.html'
    context_object_name = 'room'

    def get_queryset(self):
        return self.request.user.chat_rooms.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room = self.get_object()
        context['messages'] = room.messages.all().order_by('timestamp')
        context['participants'] = room.participants.all()
        return context


class ChatInterfaceView(LoginRequiredMixin, TemplateView):
    template_name = 'communications/chat_interface.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room_id = self.kwargs.get('room_id')
        
        try:
            room = ChatRoom.objects.get(id=room_id)
            if not room.participants.filter(id=self.request.user.id).exists():
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("You are not a participant of this room.")
            
            context['room'] = room
            context['messages'] = room.messages.all().order_by('timestamp')
            context['participants'] = room.participants.all()
        except ChatRoom.DoesNotExist:
            context['error'] = "Room not found"
        
        return context


class ChatHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'communications/chat_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room_id = self.kwargs.get('room_id')
        
        try:
            room = ChatRoom.objects.get(id=room_id)
            if not room.participants.filter(id=self.request.user.id).exists():
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("You are not a participant of this room.")
            
            context['room'] = room
            context['messages'] = room.messages.all().order_by('timestamp')
        except ChatRoom.DoesNotExist:
            context['error'] = "Room not found"
        
        return context


class MessageSearchView(LoginRequiredMixin, TemplateView):
    template_name = 'communications/message_search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get('q', '')
        
        if search_query:
            user_room_ids = self.request.user.chat_rooms.values_list('id', flat=True)
            messages = ChatMessage.objects.filter(
                room_id__in=user_room_ids,
                content__icontains=search_query
            ).select_related('sender', 'room').order_by('-timestamp')
        else:
            messages = ChatMessage.objects.none()
            
        context['messages'] = messages
        context['search_query'] = search_query
        return context


class ExportChatHistoryView(LoginRequiredMixin, TemplateView):
    template_name = 'communications/export_chat.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room_id = self.request.GET.get('room_id')
        
        if room_id:
            try:
                room = ChatRoom.objects.get(id=room_id)
                if room.participants.filter(id=self.request.user.id).exists():
                    context['room'] = room
                    context['messages'] = room.messages.all().order_by('timestamp')
            except ChatRoom.DoesNotExist:
                context['error'] = "Room not found"
        
        return context
