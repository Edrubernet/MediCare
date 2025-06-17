from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('message', _('New Message')),
        ('appointment', _('Appointment Reminder')),
        ('exercise', _('Exercise Reminder')),
        ('progress', _('Progress Update')),
        ('system', _('System Notification')),
    )

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()}"


class NotificationSetting(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='notification_settings')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    push_notifications = models.BooleanField(default=True)
    message_notifications = models.BooleanField(default=True)
    appointment_reminders = models.BooleanField(default=True)
    exercise_reminders = models.BooleanField(default=True)
    progress_updates = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Notification Setting')
        verbose_name_plural = _('Notification Settings')

    def __str__(self):
        return f"Notification Settings for {self.user.get_full_name()}"


class Reminder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reminders')
    title = models.CharField(max_length=255)
    message = models.TextField()
    scheduled_time = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Reminder')
        verbose_name_plural = _('Reminders')
        ordering = ['scheduled_time']

    def __str__(self):
        return f"{self.title} - {self.scheduled_time}"