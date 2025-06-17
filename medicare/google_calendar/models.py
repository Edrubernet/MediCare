from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class GoogleCalendarCredentials(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='google_calendar_credentials')
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Google Calendar Credentials')
        verbose_name_plural = _('Google Calendar Credentials')

    def __str__(self):
        return f"Google Calendar credentials for {self.user.get_full_name()}"


class GoogleCalendarEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='google_calendar_events')
    google_event_id = models.CharField(max_length=255)
    consultation = models.OneToOneField('consultation.Consultation', on_delete=models.CASCADE,
                                        related_name='google_event', blank=True, null=True)
    event_summary = models.CharField(max_length=255)
    event_description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced = models.DateTimeField()

    class Meta:
        verbose_name = _('Google Calendar Event')
        verbose_name_plural = _('Google Calendar Events')
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.event_summary} - {self.start_time}"