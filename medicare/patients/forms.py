from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import PatientProfile, MedicalHistory, RehabilitationHistory
from staff.models import StaffProfile

User = get_user_model()


class PatientProfileForm(forms.ModelForm):
    # User fields
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Ім'я"
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Прізвище'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )

    class Meta:
        model = PatientProfile
        fields = [
            'date_of_birth', 'gender', 'address', 
            'emergency_contact_name', 'emergency_contact_phone',
            'assigned_doctors'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Повна адреса проживання'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Ім'я контактної особи"
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+380XXXXXXXXX'
            }),
            'assigned_doctors': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        
        # Якщо редагуємо існуючого пацієнта, заповнюємо поля користувача
        if instance and instance.user:
            self.fields['first_name'].initial = instance.user.first_name
            self.fields['last_name'].initial = instance.user.last_name
            self.fields['email'].initial = instance.user.email
        
        # Фільтруємо лікарів
        self.fields['assigned_doctors'].queryset = StaffProfile.objects.filter(
            user__user_type='doctor',
            user__is_active=True
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        instance = getattr(self, 'instance', None)
        
        # Перевіряємо унікальність email
        if User.objects.filter(email=email).exclude(
            pk=instance.user.pk if instance and instance.user else None
        ).exists():
            raise ValidationError('Користувач з таким email вже існує')
        
        return email

    def clean_emergency_contact_phone(self):
        phone = self.cleaned_data.get('emergency_contact_phone')
        if phone:
            # Базова валідація номера телефону
            phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not phone.startswith('+380') and not phone.startswith('380') and not phone.startswith('0'):
                raise ValidationError('Введіть коректний український номер телефону')
        return phone

    def save(self, commit=True):
        patient = super().save(commit=False)
        
        # Оновлюємо дані користувача
        if patient.user:
            patient.user.first_name = self.cleaned_data['first_name']
            patient.user.last_name = self.cleaned_data['last_name']
            patient.user.email = self.cleaned_data['email']
            if commit:
                patient.user.save()
        
        if commit:
            patient.save()
            self.save_m2m()
        
        return patient


class MedicalHistoryForm(forms.ModelForm):
    class Meta:
        model = MedicalHistory
        fields = ['conditions', 'allergies', 'medications', 'surgeries', 'family_history']
        widgets = {
            'conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишіть хронічні захворювання, діагнози...'
            }),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Укажіть відомі алергічні реакції на медикаменти, їжу, інше...'
            }),
            'medications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Список поточних медикаментів з дозуванням та частотою прийому...'
            }),
            'surgeries': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишіть попередні хірургічні втручання з датами...'
            }),
            'family_history': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Спадкові захворювання в родині...'
            })
        }


class RehabilitationHistoryForm(forms.ModelForm):
    class Meta:
        model = RehabilitationHistory
        fields = ['injury_type', 'injury_date', 'diagnosis', 'notes', 'doctor']
        widgets = {
            'injury_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Тип травми або захворювання'
            }),
            'injury_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'diagnosis': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Детальний діагноз...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Додаткові нотатки (опціонально)...'
            }),
            'doctor': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Фільтруємо лікарів
        self.fields['doctor'].queryset = StaffProfile.objects.filter(
            user__user_type='doctor',
            user__is_active=True
        )
        self.fields['doctor'].empty_label = "Оберіть лікаря"


class PatientSearchForm(forms.Form):
    SORT_CHOICES = [
        ('user__last_name', 'За прізвищем (А-Я)'),
        ('-user__last_name', 'За прізвищем (Я-А)'),
        ('user__first_name', 'За іменем (А-Я)'),
        ('-user__first_name', 'За іменем (Я-А)'),
        ('date_of_birth', 'За віком (молодші)'),
        ('-date_of_birth', 'За віком (старші)'),
        ('-user__date_joined', 'За датою реєстрації (нові)'),
        ('user__date_joined', 'За датою реєстрації (старі)'),
    ]

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Пошук за іменем, прізвищем або email..."
        })
    )
    
    gender = forms.ChoiceField(
        choices=[
            ('', 'Всі'),
            ('M', 'Чоловіки'),
            ('F', 'Жінки'),
            ('O', 'Інше'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    assigned_doctor = forms.ModelChoiceField(
        queryset=StaffProfile.objects.filter(user__user_type='doctor'),
        required=False,
        empty_label="Всі лікарі",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    age_from = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Від (років)'
        })
    )
    
    age_to = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'До (років)'
        })
    )
    
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='user__last_name',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean(self):
        cleaned_data = super().clean()
        age_from = cleaned_data.get('age_from')
        age_to = cleaned_data.get('age_to')
        
        if age_from and age_to and age_from > age_to:
            raise ValidationError('Вік "від" не може бути більшим за вік "до"')
        
        return cleaned_data


class QuickPatientForm(forms.ModelForm):
    """Спрощена форма для швидкого додавання пацієнта"""
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Ім'я *"
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Прізвище *'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email *'
        })
    )

    class Meta:
        model = PatientProfile
        fields = ['date_of_birth', 'gender']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def save(self, commit=True):
        # Спочатку створюємо користувача
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            user_type='patient'
        )
        
        # Потім створюємо профіль пацієнта
        patient = super().save(commit=False)
        patient.user = user
        
        if commit:
            patient.save()
        
        return patient