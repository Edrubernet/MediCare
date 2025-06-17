from rest_framework import serializers
from .models import ChatRoom, ChatMessage
from staff.serializers import UserSerializer


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'room', 'sender', 'content', 'timestamp']


class ChatRoomSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    messages = ChatMessageSerializer(many=True, read_only=True, source='messages.all') # Get all messages

    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'participants', 'messages', 'created_at', 'updated_at']


class ChatRoomListSerializer(serializers.ModelSerializer):
    """
    A light serializer for listing chat rooms, showing only the last message.
    """
    last_message = serializers.SerializerMethodField()
    participants = UserSerializer(many=True, read_only=True)

    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'participants', 'last_message', 'updated_at']

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('timestamp').last()
        if last_msg:
            return ChatMessageSerializer(last_msg).data
        return None 