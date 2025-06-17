from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class PatientProfile(models.Model):
    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    assigned_doctors = models.ManyToManyField('staff.StaffProfile', related_name='patients', blank=True)

    class Meta:
        verbose_name = _('Patient Profile')
        verbose_name_plural = _('Patient Profiles')

    def __str__(self):
        return self.user.get_full_name()


class MedicalHistory(models.Model):
    patient = models.OneToOneField(PatientProfile, on_delete=models.CASCADE, related_name='medical_history')
    conditions = models.TextField(blank=True, null=True, help_text=_('Pre-existing medical conditions'))
    allergies = models.TextField(blank=True, null=True)
    medications = models.TextField(blank=True, null=True, help_text=_('Current medications'))
    surgeries = models.TextField(blank=True, null=True, help_text=_('Previous surgeries'))
    family_history = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('Medical History')
        verbose_name_plural = _('Medical Histories')

    def __str__(self):
        return f"{self.patient}'s Medical History"


class RehabilitationHistory(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='rehabilitation_history')
    injury_type = models.CharField(max_length=255)
    injury_date = models.DateField()
    diagnosis = models.TextField()
    notes = models.TextField(blank=True, null=True)
    doctor = models.ForeignKey('staff.StaffProfile', on_delete=models.SET_NULL, null=True, related_name='diagnoses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Rehabilitation History')
        verbose_name_plural = _('Rehabilitation Histories')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient} - {self.injury_type}"