import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage
from staff.models import User
from .serializers import ChatMessageSerializer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return
        
        is_participant = await self.is_user_participant(self.user, self.room_id)
        if not is_participant:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']

        # Create new message object
        new_message = await self.create_chat_message(
            room_id=self.room_id,
            sender=self.user,
            content=message_content
        )

        # Serialize the message
        serialized_message = ChatMessageSerializer(new_message).data

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': serialized_message
            }
        )

    # Receive message from room group and send to WebSocket
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(message))

    @database_sync_to_async
    def is_user_participant(self, user, room_id):
        try:
            room = ChatRoom.objects.get(id=room_id)
            return room.participants.filter(id=user.id).exists()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def create_chat_message(self, room_id, sender, content):
        room = ChatRoom.objects.get(id=room_id)
        # also update the room's updated_at timestamp
        room.save()
        return ChatMessage.objects.create(room=room, sender=sender, content=content) 