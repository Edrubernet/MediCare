from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ChatRoom(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, through='ChatParticipant', related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Chat Room')
        verbose_name_plural = _('Chat Rooms')
        ordering = ['-updated_at']

    def __str__(self):
        return self.name or f"Chat Room {self.id}"


class ChatParticipant(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    last_read_timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'room')


class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Chat Message')
        verbose_name_plural = _('Chat Messages')
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender} in {self.room}"
