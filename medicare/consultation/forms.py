from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Consultation, ConsultationNote
from patients.models import PatientProfile
from staff.models import StaffProfile


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = [
            'patient', 'doctor', 'start_time', 'end_time', 
            'consultation_type', 'video_link', 'notes'
        ]
        widgets = {
            'patient': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_patient'
            }),
            'doctor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'end_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'consultation_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'video_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://meet.google.com/...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Додаткові нотатки (опціонально)'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.user = user  # Зберігаємо user для використання в clean методах
        
        # Спочатку показуємо всіх активних пацієнтів (для тестування)
        all_patients = PatientProfile.objects.filter(
            user__is_active=True
        ).select_related('user')
        
        self.fields['patient'].queryset = all_patients
        
        # Додаємо choices вручну для кращої відображення
        patient_choices = [('', '---------')]
        for patient in all_patients:
            patient_choices.append((
                patient.id, 
                f"{patient.user.get_full_name()} ({patient.user.email})"
            ))
        
        self.fields['patient'].choices = patient_choices
        
        # Фільтруємо лікарів
        self.fields['doctor'].queryset = StaffProfile.objects.filter(
            user__user_type='doctor',
            user__is_active=True
        ).select_related('user')
        
        # Встановлюємо поточного лікаря як default та обробляємо логіку видимості
        if user and hasattr(user, 'staff_profile') and user.user_type == 'doctor':
            self.fields['doctor'].initial = user.staff_profile
            # Для звичайних лікарів робимо поле обов'язковим та попередньо заповненим
            if not user.is_staff:
                # Робимо поле приховане для звичайних лікарів
                self.fields['doctor'].widget = forms.HiddenInput()
                self.fields['doctor'].required = False  # Зробимо його необов'язковим

    def clean_doctor(self):
        doctor = self.cleaned_data.get('doctor')
        # Якщо лікар не вказаний, але форма ініціалізована з user, то використовуємо його
        if not doctor and hasattr(self, 'user') and self.user and hasattr(self.user, 'staff_profile'):
            if self.user.user_type == 'doctor':
                return self.user.staff_profile
        return doctor

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            # Перевіряємо, що час початку раніше часу завершення
            if start_time >= end_time:
                raise ValidationError('Час початку повинен бути раніше часу завершення')
            
            # Перевіряємо, що консультація не в минулому
            if start_time < timezone.now():
                raise ValidationError('Не можна планувати консультацію в минулому')
            
            # Перевіряємо тривалість (не більше 8 годин)
            duration = end_time - start_time
            if duration.total_seconds() > 8 * 60 * 60:
                raise ValidationError('Тривалість консультації не може перевищувати 8 годин')
            
            # Перевіряємо конфлікти з іншими консультаціями
            doctor = cleaned_data.get('doctor')
            if doctor:
                conflicts = Consultation.objects.filter(
                    doctor=doctor,
                    start_time__lt=end_time,
                    end_time__gt=start_time,
                    status__in=['scheduled', 'in_progress']
                ).exclude(pk=self.instance.pk if self.instance else None)
                
                if conflicts.exists():
                    raise ValidationError('У цей час у лікаря вже заплановано іншу консультацію')
        
        # Валідація відео-посилання для онлайн консультацій
        consultation_type = cleaned_data.get('consultation_type')
        video_link = cleaned_data.get('video_link')
        
        if consultation_type == 'video' and not video_link:
            raise ValidationError('Для відео консультації необхідно вказати посилання')
        
        return cleaned_data


class QuickConsultationForm(forms.ModelForm):
    """Спрощена форма для швидкого планування консультації"""
    
    class Meta:
        model = Consultation
        fields = ['patient', 'start_time', 'consultation_type']
        widgets = {
            'patient': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'consultation_type': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Фільтруємо пацієнтів для поточного лікаря
        if user and user.user_type == 'doctor' and hasattr(user, 'staff_profile'):
            patients_qs = PatientProfile.objects.filter(
                assigned_doctors=user.staff_profile,
                user__is_active=True
            ).select_related('user')
        else:
            patients_qs = PatientProfile.objects.filter(
                user__is_active=True
            ).select_related('user')
        
        self.fields['patient'].queryset = patients_qs
        
        # Встановлюємо початковий час (наступний вільний слот)
        next_hour = timezone.now().replace(minute=0, second=0, microsecond=0) + timezone.timedelta(hours=1)
        self.fields['start_time'].initial = next_hour

    def save(self, commit=True):
        consultation = super().save(commit=False)
        
        # Автоматично встановлюємо час завершення (1 година)
        if consultation.start_time:
            consultation.end_time = consultation.start_time + timezone.timedelta(hours=1)
        
        # Встановлюємо статус
        consultation.status = 'scheduled'
        
        if commit:
            consultation.save()
        
        return consultation


class ConsultationNoteForm(forms.ModelForm):
    class Meta:
        model = ConsultationNote
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Введіть нотатки про консультацію...'
            })
        }


class ConsultationSearchForm(forms.Form):
    SORT_CHOICES = [
        ('-start_time', 'За датою (нові спочатку)'),
        ('start_time', 'За датою (старі спочатку)'),
        ('patient__user__last_name', 'За пацієнтом (А-Я)'),
        ('-patient__user__last_name', 'За пацієнтом (Я-А)'),
        ('status', 'За статусом'),
    ]

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пошук за пацієнтом...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Всі статуси')] + list(Consultation.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    consultation_type = forms.ChoiceField(
        choices=[
            ('', 'Всі типи'),
            ('video', 'Відео консультація'),
            ('in_person', 'Особиста консультація'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-start_time',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError('Дата "від" не може бути пізніше дати "до"')
        
        return cleaned_data


class PatientConsultationRequestForm(forms.ModelForm):
    """Форма для запиту консультації пацієнтом"""
    
    class Meta:
        model = Consultation
        fields = ['doctor', 'start_time', 'consultation_type', 'notes']
        widgets = {
            'doctor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'consultation_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опишіть причину візиту (опціонально)'
            })
        }

    def __init__(self, *args, **kwargs):
        patient = kwargs.pop('patient', None)
        super().__init__(*args, **kwargs)
        
        # Спочатку показуємо призначених лікарів, якщо вони є
        assigned_doctors = None
        if patient:
            assigned_doctors = patient.assigned_doctors.filter(
                user__is_active=True
            ).select_related('user')
        
        # Якщо немає призначених лікарів, показуємо всіх активних лікарів
        if not assigned_doctors or not assigned_doctors.exists():
            self.fields['doctor'].queryset = StaffProfile.objects.filter(
                user__user_type='doctor',
                user__is_active=True
            ).select_related('user')
            all_doctors = self.fields['doctor'].queryset
        else:
            self.fields['doctor'].queryset = assigned_doctors
            all_doctors = assigned_doctors
        
        # Додаємо choices для лікарів
        doctor_choices = [('', 'Виберіть лікаря')]
        for doctor in all_doctors:
            specialization = getattr(doctor, 'specialization', 'Лікар') or 'Лікар'
            doctor_choices.append((
                doctor.id,
                f"Д-р {doctor.user.get_full_name()} ({specialization})"
            ))
        
        self.fields['doctor'].choices = doctor_choices

    def save(self, commit=True):
        consultation = super().save(commit=False)
        
        # Автоматично встановлюємо час завершення (1 година)
        if consultation.start_time:
            consultation.end_time = consultation.start_time + timezone.timedelta(hours=1)
        
        if commit:
            consultation.save()
        
        return consultation