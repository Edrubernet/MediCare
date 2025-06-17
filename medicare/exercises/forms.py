from django import forms
from django.core.exceptions import ValidationError
from .models import (
    BodyPart, ExerciseCategory, DifficultyLevel, Exercise, 
    ExerciseImage, ExerciseStep, EducationalMaterial
)


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = [
            'title', 'description', 'body_parts', 'categories', 
            'difficulty', 'video', 'video_thumbnail', 'instructions', 
            'precautions', 'is_public'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва вправи'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опис вправи'
            }),
            'body_parts': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'categories': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'form-select'
            }),
            'video': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*'
            }),
            'video_thumbnail': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Детальні інструкції виконання вправи'
            }),
            'precautions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Застереження та обмеження (опціонально)'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_video(self):
        video = self.cleaned_data.get('video')
        if video:
            # Перевірка розміру файлу (максимум 100MB)
            if video.size > 100 * 1024 * 1024:
                raise ValidationError('Розмір відео файлу не повинен перевищувати 100MB')
            
            # Перевірка типу файлу
            allowed_types = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv']
            if hasattr(video, 'content_type') and video.content_type not in allowed_types:
                raise ValidationError('Підтримуються лише відео файли форматів: MP4, AVI, MOV, WMV')
        
        return video

    def clean_video_thumbnail(self):
        thumbnail = self.cleaned_data.get('video_thumbnail')
        if thumbnail:
            # Перевірка розміру файлу (максимум 5MB)
            if thumbnail.size > 5 * 1024 * 1024:
                raise ValidationError('Розмір зображення не повинен перевищувати 5MB')
            
            # Перевірка типу файлу
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if hasattr(thumbnail, 'content_type') and thumbnail.content_type not in allowed_types:
                raise ValidationError('Підтримуються лише зображення форматів: JPEG, PNG, GIF')
        
        return thumbnail


class ExerciseStepForm(forms.ModelForm):
    class Meta:
        model = ExerciseStep
        fields = ['step_number', 'instruction', 'image']
        widgets = {
            'step_number': forms.HiddenInput(),
            'instruction': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опишіть цей крок детально...'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Перевірка розміру файлу (максимум 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('Розмір зображення не повинен перевищувати 5MB')
            
            # Перевірка типу файлу
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise ValidationError('Підтримуються лише зображення форматів: JPEG, PNG, GIF')
        
        return image


class ExerciseImageForm(forms.ModelForm):
    class Meta:
        model = ExerciseImage
        fields = ['image', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Опис зображення (опціонально)'
            })
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # Перевірка розміру файлу (максимум 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('Розмір зображення не повинен перевищувати 5MB')
            
            # Перевірка типу файлу
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if hasattr(image, 'content_type') and image.content_type not in allowed_types:
                raise ValidationError('Підтримуються лише зображення форматів: JPEG, PNG, GIF')
        
        return image


class EducationalMaterialForm(forms.ModelForm):
    class Meta:
        model = EducationalMaterial
        fields = ['title', 'description', 'file', 'file_type', 'related_exercises']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва матеріалу'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опис навчального матеріалу'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'file_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'related_exercises': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Перевірка розміру файлу (максимум 50MB)
            if file.size > 50 * 1024 * 1024:
                raise ValidationError('Розмір файлу не повинен перевищувати 50MB')
        
        return file


class ExerciseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExerciseCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва категорії'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Опис категорії'
            })
        }


class BodyPartForm(forms.ModelForm):
    class Meta:
        model = BodyPart
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва частини тіла'
            })
        }


class DifficultyLevelForm(forms.ModelForm):
    class Meta:
        model = DifficultyLevel
        fields = ['name', 'value']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва рівня складності'
            }),
            'value': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': 'Числове значення (1-10)'
            })
        }

    def clean_value(self):
        value = self.cleaned_data.get('value')
        if value is not None:
            if value < 1 or value > 10:
                raise ValidationError('Значення повинно бути від 1 до 10')
            
            # Перевірка унікальності значення
            if DifficultyLevel.objects.filter(value=value).exclude(pk=self.instance.pk).exists():
                raise ValidationError(f'Рівень складності зі значенням {value} вже існує')
        
        return value


class ExerciseSearchForm(forms.Form):
    SORT_CHOICES = [
        ('title', 'За назвою (А-Я)'),
        ('-title', 'За назвою (Я-А)'),
        ('created_at', 'За датою створення (старі)'),
        ('-created_at', 'За датою створення (нові)'),
        ('difficulty__value', 'За складністю (легкі)'),
        ('-difficulty__value', 'За складністю (складні)'),
    ]

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пошук за назвою або описом...'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=ExerciseCategory.objects.all(),
        required=False,
        empty_label="Всі категорії",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    body_part = forms.ModelChoiceField(
        queryset=BodyPart.objects.all(),
        required=False,
        empty_label="Всі частини тіла",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    difficulty = forms.ModelChoiceField(
        queryset=DifficultyLevel.objects.all(),
        required=False,
        empty_label="Всі рівні складності",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_public = forms.ChoiceField(
        choices=[
            ('', 'Всі вправи'),
            ('True', 'Тільки публічні'),
            ('False', 'Тільки приватні'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )