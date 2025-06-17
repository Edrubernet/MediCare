from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', _('Administrator')),
        ('doctor', _('Therapist')),
        ('patient', _('Patient')),
    )

    patronymic = models.CharField(_("По батькові"), max_length=150, blank=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    
    # Поля безпеки
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    last_password_change = models.DateTimeField(null=True, blank=True)
    must_change_password = models.BooleanField(default=False)
    
    # Медичні дані (шифровані)
    is_medical_data_encrypted = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        permissions = [
            ('view_all_patients', 'Can view all patients'),
            ('manage_medical_data', 'Can manage medical data'),
            ('assign_exercises', 'Can assign exercises'),
            ('view_reports', 'Can view reports'),
        ]
    
    def save(self, *args, **kwargs):
        # Автоматично генеруємо username якщо його немає
        if not self.username and self.first_name and self.last_name:
            from django.utils.text import slugify
            import uuid
            base_username = slugify(f"{self.first_name}.{self.last_name}", allow_unicode=True)
            # Перевіряємо унікальність
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}.{counter}"
                counter += 1
            self.username = username
        
        # Автоматично оновлюємо last_password_change при створенні користувача
        if not self.pk and not self.last_password_change:
            from django.utils import timezone
            self.last_password_change = timezone.now()
        super().save(*args, **kwargs)
    
    def set_password(self, raw_password):
        super().set_password(raw_password)
        from django.utils import timezone
        self.last_password_change = timezone.now()


class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    specialization = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    certificates = models.ManyToManyField('Certificate', blank=True)

    class Meta:
        verbose_name = _('Staff Profile')
        verbose_name_plural = _('Staff Profiles')

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.specialization}"


class Certificate(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='certificates/')
    issue_date = models.DateField()

    class Meta:
        verbose_name = _('Certificate')
        verbose_name_plural = _('Certificates')

    def __str__(self):
        return self.name


class WorkSchedule(models.Model):
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='work_schedules')
    day_of_week = models.IntegerField(choices=[(i, _(day)) for i, day in enumerate(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])])
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        verbose_name = _('Work Schedule')
        verbose_name_plural = _('Work Schedules')
        unique_together = ('staff', 'day_of_week')

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.get_day_of_week_display()}"


