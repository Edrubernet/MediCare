from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Consultation(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Запланована'),
        ('in_progress', 'Триває'),
        ('completed', 'Завершена'),
        ('canceled', 'Скасована'),
    )

    patient = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE, related_name='consultations')
    doctor = models.ForeignKey('staff.StaffProfile', on_delete=models.CASCADE, related_name='consultations')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    CONSULTATION_TYPE_CHOICES = [
        ('video', 'Відео консультація'),
        ('in_person', 'Особиста консультація'),
    ]
    
    consultation_type = models.CharField(max_length=20, choices=CONSULTATION_TYPE_CHOICES)
    video_link = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Consultation')
        verbose_name_plural = _('Consultations')
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.patient} with {self.doctor.user.get_full_name()} - {self.start_time}"


class ConsultationNote(models.Model):
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name='consultation_note')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Consultation Note')
        verbose_name_plural = _('Consultation Notes')

    def __str__(self):
        return f"Notes for {self.consultation}"


class ConsultationRecording(models.Model):
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name='recording')
    file = models.FileField(upload_to='consultation_recordings/')
    duration = models.PositiveIntegerField(help_text=_('Duration in seconds'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Consultation Recording')
        verbose_name_plural = _('Consultation Recordings')

    def __str__(self):
        return f"Recording for {self.consultation}"