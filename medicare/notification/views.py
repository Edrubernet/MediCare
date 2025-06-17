from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, TemplateView
from django.views import View
from django.http import JsonResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

# Create your views here.

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to view notifications.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the notifications
        for the currently authenticated user.
        """
        return self.queryset.filter(recipient=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark a specific notification as read.
        """
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        Mark all notifications for the user as read.
        """
        self.get_queryset().update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


# Web Views (Class-Based Views for notification management)
class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notification/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = self.get_queryset().filter(is_read=False).count()
        return context


class UnreadNotificationView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notification/unread_notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).order_by('-created_at')


class MarkAllReadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('notification:notification_list')


class MarkReadView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        try:
            notification = Notification.objects.get(
                pk=pk,
                recipient=request.user
            )
            notification.is_read = True
            notification.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            
        except Notification.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Notification not found'})
        
        return redirect('notification:notification_list')


class NotificationSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'notification/settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add user notification settings if they exist in user profile
        user = self.request.user
        if hasattr(user, 'notification_settings'):
            context['settings'] = user.notification_settings
        return context


class NotificationPreferencesView(LoginRequiredMixin, TemplateView):
    template_name = 'notification/preferences.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add notification preferences context
        context['email_notifications'] = getattr(user, 'email_notifications_enabled', True)
        context['push_notifications'] = getattr(user, 'push_notifications_enabled', True)
        context['sms_notifications'] = getattr(user, 'sms_notifications_enabled', False)
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Handle preference updates
        user = request.user
        
        # Update notification preferences based on form data
        email_enabled = request.POST.get('email_notifications') == 'on'
        push_enabled = request.POST.get('push_notifications') == 'on'
        sms_enabled = request.POST.get('sms_notifications') == 'on'
        
        # If user profile has notification settings fields, update them
        if hasattr(user, 'email_notifications_enabled'):
            user.email_notifications_enabled = email_enabled
        if hasattr(user, 'push_notifications_enabled'):
            user.push_notifications_enabled = push_enabled
        if hasattr(user, 'sms_notifications_enabled'):
            user.sms_notifications_enabled = sms_enabled
        
        user.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('notification:notification_preferences')
