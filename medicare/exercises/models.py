from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class BodyPart(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = _('Body Part')
        verbose_name_plural = _('Body Parts')

    def __str__(self):
        return self.name


class ExerciseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('Exercise Category')
        verbose_name_plural = _('Exercise Categories')

    def __str__(self):
        return self.name


class DifficultyLevel(models.Model):
    name = models.CharField(max_length=50)
    value = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        verbose_name = _('Difficulty Level')
        verbose_name_plural = _('Difficulty Levels')
        ordering = ['value']

    def __str__(self):
        return self.name


class Exercise(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    body_parts = models.ManyToManyField(BodyPart, related_name='exercises')
    categories = models.ManyToManyField(ExerciseCategory, related_name='exercises')
    difficulty = models.ForeignKey(DifficultyLevel, on_delete=models.SET_NULL, null=True)
    video = models.FileField(upload_to='exercise_videos/', blank=True, null=True)
    video_thumbnail = models.ImageField(upload_to='exercise_thumbnails/', blank=True, null=True)
    instructions = models.TextField()
    precautions = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='created_exercises')
    is_public = models.BooleanField(default=True, help_text=_('If true, exercise is available to all doctors'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Exercise')
        verbose_name_plural = _('Exercises')
        ordering = ['title']

    def __str__(self):
        return self.title


class ExerciseStep(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='steps')
    step_number = models.PositiveIntegerField()
    instruction = models.TextField(help_text=_('Detailed instruction for this step'))
    image = models.ImageField(upload_to='exercise_step_images/', blank=True, null=True, 
                             help_text=_('Optional image for this step'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Exercise Step')
        verbose_name_plural = _('Exercise Steps')
        ordering = ['step_number']
        unique_together = ['exercise', 'step_number']

    def __str__(self):
        return f"Step {self.step_number} for {self.exercise.title}"


class ExerciseImage(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='exercise_images/')
    caption = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _('Exercise Image')
        verbose_name_plural = _('Exercise Images')

    def __str__(self):
        return f"Image for {self.exercise.title}"


class EducationalMaterial(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    file = models.FileField(upload_to='educational_materials/')
    file_type = models.CharField(max_length=20, choices=[
        ('pdf', 'PDF'),
        ('video', 'Video'),
        ('article', 'Article'),
        ('other', 'Other')
    ])
    related_exercises = models.ManyToManyField(Exercise, related_name='educational_materials', blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                   related_name='created_materials')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Educational Material')
        verbose_name_plural = _('Educational Materials')
        ordering = ['-created_at']

    def __str__(self):
        return self.title