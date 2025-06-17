from django import forms
from django.forms import inlineformset_factory
from .models import Survey, Question, QuestionOption, SurveyResponse, QuestionResponse, SurveyAssignment


class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = ['title', 'description', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введіть назву опитування'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опис опитування (необов\'язково)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type', 'required', 'order']
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Текст питання'
            }),
            'question_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'required': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            })
        }


QuestionFormSet = inlineformset_factory(
    Survey, 
    Question, 
    form=QuestionForm,
    extra=1,
    can_delete=True,
    fields=['text', 'question_type', 'required', 'order']
)


class QuestionOptionForm(forms.ModelForm):
    class Meta:
        model = QuestionOption
        fields = ['text', 'order']
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Текст варіанту відповіді'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            })
        }


class ResponseForm(forms.Form):
    """Динамічна форма для відповідей на опитування"""
    
    def __init__(self, survey, *args, **kwargs):
        self.survey = survey
        super().__init__(*args, **kwargs)
        
        # Створюємо поля для кожного питання
        for question in survey.questions.all().order_by('order'):
            field_name = f'question_{question.id}'
            
            if question.question_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=question.text,
                    required=question.required,
                    widget=forms.Textarea(attrs={
                        'class': 'form-control',
                        'rows': 3,
                        'placeholder': 'Введіть вашу відповідь'
                    })
                )
            
            elif question.question_type == 'rating':
                self.fields[field_name] = forms.ChoiceField(
                    label=question.text,
                    required=question.required,
                    choices=[(i, str(i)) for i in range(1, 11)],
                    widget=forms.RadioSelect(attrs={
                        'class': 'form-check-input'
                    })
                )
            
            elif question.question_type == 'yes_no':
                self.fields[field_name] = forms.ChoiceField(
                    label=question.text,
                    required=question.required,
                    choices=[('yes', 'Так'), ('no', 'Ні')],
                    widget=forms.RadioSelect(attrs={
                        'class': 'form-check-input'
                    })
                )
            
            elif question.question_type == 'single_choice':
                choices = [(option.id, option.text) for option in question.options.all().order_by('order')]
                self.fields[field_name] = forms.ChoiceField(
                    label=question.text,
                    required=question.required,
                    choices=choices,
                    widget=forms.RadioSelect(attrs={
                        'class': 'form-check-input'
                    })
                )
            
            elif question.question_type == 'multiple_choice':
                choices = [(option.id, option.text) for option in question.options.all().order_by('order')]
                self.fields[field_name] = forms.MultipleChoiceField(
                    label=question.text,
                    required=question.required,
                    choices=choices,
                    widget=forms.CheckboxSelectMultiple(attrs={
                        'class': 'form-check-input'
                    })
                )


class SurveyFilterForm(forms.Form):
    """Форма для фільтрації опитувань"""
    
    ACTIVE_CHOICES = [
        ('', 'Всі'),
        ('true', 'Активні'),
        ('false', 'Неактивні'),
    ]
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пошук по назві або опису'
        })
    )
    
    active = forms.ChoiceField(
        choices=ACTIVE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class AssignmentFilterForm(forms.Form):
    """Форма для фільтрації призначень"""
    
    STATUS_CHOICES = [('', 'Всі')] + list(SurveyAssignment.STATUS_CHOICES)
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пошук по назві опитування або пацієнту'
        })
    )


class SurveyAssignForm(forms.Form):
    """Форма для призначення опитування"""
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        # Опитування, створені поточним користувачем
        self.fields['survey'] = forms.ModelChoiceField(
            queryset=Survey.objects.filter(created_by=user, is_active=True),
            empty_label='Виберіть опитування',
            widget=forms.Select(attrs={
                'class': 'form-select'
            })
        )
        
        # Пацієнти
        from patients.models import PatientProfile
        self.fields['patients'] = forms.ModelMultipleChoiceField(
            queryset=PatientProfile.objects.all(),
            widget=forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            })
        )
    
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Додаткові нотатки (необов\'язково)'
        })
    )


class BulkAssignmentActionForm(forms.Form):
    """Форма для масових дій з призначеннями"""
    
    ACTION_CHOICES = [
        ('', 'Виберіть дію'),
        ('mark_completed', 'Позначити як завершені'),
        ('mark_expired', 'Позначити як прострочені'),
        ('delete', 'Видалити'),
        ('extend_due_date', 'Продовжити термін виконання'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    assignment_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    new_due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class QuestionAnalysisForm(forms.Form):
    """Форма для аналізу результатів питань"""
    
    ANALYSIS_TYPE_CHOICES = [
        ('basic', 'Базова статистика'),
        ('detailed', 'Детальний аналіз'),
        ('comparative', 'Порівняльний аналіз'),
    ]
    
    analysis_type = forms.ChoiceField(
        choices=ANALYSIS_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
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
    
    include_incomplete = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )