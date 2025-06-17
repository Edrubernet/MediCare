from django import forms
from django.db import models
from django.core.exceptions import ValidationError
from .models import RehabilitationProgram, ProgramExercise
from patients.models import PatientProfile
from exercises.models import Exercise
from staff.models import StaffProfile


class RehabilitationProgramForm(forms.ModelForm):
    class Meta:
        model = RehabilitationProgram
        fields = [
            'title', 'description', 'patient', 'doctor', 'start_date', 
            'end_date', 'status', 'goals', 'expected_outcomes', 'sessions_per_week', 'session_duration'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва програми реабілітації'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опис програми та основні цілі'
            }),
            'patient': forms.Select(attrs={
                'class': 'form-select'
            }),
            'doctor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'goals': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Конкретні цілі та очікувані результати'
            }),
            'expected_outcomes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Очікувані результати'
            }),
            'sessions_per_week': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 7,
                'placeholder': 'Кількість сесій на тиждень'
            }),
            'session_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 15,
                'max': 180,
                'placeholder': 'Тривалість сесії (хв)'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Фільтруємо пацієнтів
        self.fields['patient'].queryset = PatientProfile.objects.filter(
            user__is_active=True
        ).select_related('user')
        
        # Фільтруємо лікарів
        self.fields['doctor'].queryset = StaffProfile.objects.filter(
            user__user_type='doctor',
            user__is_active=True
        ).select_related('user')
        
        # Якщо передано користувача, встановлюємо його як створювача
        if user and hasattr(user, 'staff_profile'):
            self.fields['doctor'].initial = user.staff_profile
            self.fields['doctor'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError('Дата початку повинна бути раніше дати завершення')
        
        return cleaned_data


class ProgramExerciseForm(forms.ModelForm):
    class Meta:
        model = ProgramExercise
        fields = [
            'exercise', 'sets', 'repetitions', 'duration',
            'rest_between_sets', 'additional_instructions', 'order'
        ]
        widgets = {
            'exercise': forms.Select(attrs={
                'class': 'form-select'
            }),
            'sets': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 20,
                'placeholder': 'Кількість підходів'
            }),
            'repetitions': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100,
                'placeholder': 'Повторення в підході'
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10800,
                'placeholder': 'Тривалість (секунди)'
            }),
            'rest_between_sets': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 600,
                'placeholder': 'Відпочинок між підходами (секунди)'
            }),
            'additional_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Додаткові вказівки'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Порядок виконання'
            })
        }

    def __init__(self, *args, **kwargs):
        program = kwargs.pop('program', None)
        super().__init__(*args, **kwargs)
        
        # Фільтруємо вправи
        self.fields['exercise'].queryset = Exercise.objects.filter(
            is_public=True
        ).select_related('difficulty')
        
        # Якщо передано програму, встановлюємо наступний порядок
        if program and not self.instance.pk:
            last_order = ProgramExercise.objects.filter(
                program=program
            ).aggregate(
                max_order=models.Max('order')
            )['max_order'] or 0
            self.fields['order'].initial = last_order + 1

    def clean(self):
        cleaned_data = super().clean()
        sets = cleaned_data.get('sets')
        repetitions = cleaned_data.get('repetitions')
        duration = cleaned_data.get('duration')
        
        # Перевіряємо, що вказано або повторення, або тривалість
        if not repetitions and not duration:
            raise ValidationError(
                'Необхідно вказати або кількість повторень, або тривалість виконання'
            )
        
        return cleaned_data


class ProgramSearchForm(forms.Form):
    SORT_CHOICES = [
        ('title', 'За назвою (А-Я)'),
        ('-title', 'За назвою (Я-А)'),
        ('start_date', 'За датою початку (старі)'),
        ('-start_date', 'За датою початку (нові)'),
        ('status', 'За статусом'),
        ('patient__user__last_name', 'За пацієнтом'),
    ]

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пошук за назвою або описом...'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'Всі статуси')] + RehabilitationProgram.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    patient = forms.ModelChoiceField(
        queryset=PatientProfile.objects.all(),
        required=False,
        empty_label="Всі пацієнти",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    doctor = forms.ModelChoiceField(
        queryset=StaffProfile.objects.filter(user__user_type='doctor'),
        required=False,
        empty_label="Всі лікарі",
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
        initial='-start_date',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Оновлюємо queryset для пацієнтів з іменами
        self.fields['patient'].queryset = PatientProfile.objects.select_related(
            'user'
        ).filter(user__is_active=True)
        
        # Оновлюємо queryset для лікарів
        self.fields['doctor'].queryset = StaffProfile.objects.select_related(
            'user'
        ).filter(user__user_type='doctor', user__is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError('Дата "від" не може бути пізніше дати "до"')
        
        return cleaned_data


class QuickProgramForm(forms.ModelForm):
    """Спрощена форма для швидкого створення програми"""
    
    class Meta:
        model = RehabilitationProgram
        fields = ['title', 'description', 'patient', 'start_date', 'goals']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва програми *'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Короткий опис'
            }),
            'patient': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'goals': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Основні цілі програми'
            })
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Фільтруємо пацієнтів
        self.fields['patient'].queryset = PatientProfile.objects.filter(
            user__is_active=True
        ).select_related('user')
        
        # Встановлюємо сьогоднішню дату як початкову
        from django.utils import timezone
        self.fields['start_date'].initial = timezone.now().date()

    def save(self, commit=True):
        program = super().save(commit=False)
        
        # Встановлюємо статус як чернетка
        program.status = 'draft'
        
        if commit:
            program.save()
        
        return program


# Formset для додавання кількох вправ одночасно
from django.forms import formset_factory

ProgramExerciseFormSet = formset_factory(
    ProgramExerciseForm,
    extra=3,
    can_delete=True,
    max_num=20
)