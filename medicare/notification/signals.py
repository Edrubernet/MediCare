from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
import json


@receiver(post_save, sender=Notification)
def send_notification_on_save(sender, instance, created, **kwargs):
    """
    Send notification to user via WebSocket when a Notification object is created.
    """
    if created:
        channel_layer = get_channel_layer()
        group_name = f'notifications_{instance.recipient.id}'

        # The data that will be sent in the WebSocket message
        message_data = {
            'id': instance.id,
            'title': instance.title,
            'message': instance.message,
            'type': instance.notification_type,
            'is_read': instance.is_read,
            'created_at': instance.created_at.isoformat(),
        }

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'send_notification',  # This corresponds to the method in the consumer
                'message': message_data
            }
        ) 