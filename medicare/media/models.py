from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class MediaFile(models.Model):
    FILE_TYPES = (
        ('video', _('Video')),
        ('image', _('Image')),
        ('document', _('Document')),
        ('audio', _('Audio')),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='media_files/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    file_size = models.PositiveIntegerField(help_text=_('File size in bytes'))
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_files')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Media File')
        verbose_name_plural = _('Media Files')
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class VideoProcessingStatus(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    )

    media_file = models.OneToOneField(MediaFile, on_delete=models.CASCADE, related_name='processing_status')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.PositiveSmallIntegerField(default=0, help_text=_('Processing progress in percentage'))
    error_message = models.TextField(blank=True, null=True)
    processed_file = models.FileField(upload_to='processed_videos/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True)
    duration = models.PositiveIntegerField(blank=True, null=True, help_text=_('Duration in seconds'))
    resolution = models.CharField(max_length=20, blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('Video Processing Status')
        verbose_name_plural = _('Video Processing Statuses')

    def __str__(self):
        return f"{self.media_file.title} - {self.get_status_display()}"