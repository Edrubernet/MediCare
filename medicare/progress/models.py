from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class ExerciseSession(models.Model):
    program = models.ForeignKey('programs.RehabilitationProgram', on_delete=models.CASCADE,
                                related_name='exercise_sessions')
    patient = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE, related_name='exercise_sessions')
    date = models.DateField()
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Exercise Session')
        verbose_name_plural = _('Exercise Sessions')
        ordering = ['-date']

    def __str__(self):
        return f"{self.patient} - {self.date}"


class ExerciseCompletion(models.Model):
    session = models.ForeignKey(ExerciseSession, on_delete=models.CASCADE, related_name='exercise_completions')
    program_exercise = models.ForeignKey('programs.ProgramExercise', on_delete=models.CASCADE)
    sets_completed = models.PositiveIntegerField()
    repetitions_completed = models.PositiveIntegerField()
    pain_level = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)],
                                                  help_text=_('Pain level (0-10)'))
    difficulty_level = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)],
                                                        help_text=_('Difficulty level (0-10)'))
    notes = models.TextField(blank=True, null=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Exercise Completion')
        verbose_name_plural = _('Exercise Completions')

    def __str__(self):
        return f"{self.program_exercise.exercise.title} - {self.completed_at.date()}"



class PatientNote(models.Model):
    patient = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE, related_name='notes')
    doctor = models.ForeignKey('staff.StaffProfile', on_delete=models.CASCADE, related_name='patient_notes')
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Patient Note')
        verbose_name_plural = _('Patient Notes')
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for {self.patient} by {self.doctor.user.get_full_name()}"


class RehabilitationGoal(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    CATEGORY_CHOICES = [
        ('mobility', 'Mobility'),
        ('strength', 'Strength'),
        ('flexibility', 'Flexibility'),
        ('balance', 'Balance'),
        ('pain', 'Pain Management'),
        ('cognitive', 'Cognitive Functions'),
        ('speech', 'Speech'),
    ]
    
    patient = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE, related_name='rehabilitation_goals')
    doctor = models.ForeignKey('staff.StaffProfile', on_delete=models.CASCADE, related_name='created_goals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    current_value = models.FloatField(default=0, help_text="Current progress value")
    target_value = models.FloatField(help_text="Target value to achieve")
    unit = models.CharField(max_length=50, blank=True, help_text="Unit of measurement (e.g., minutes, repetitions)")
    
    target_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_achieved = models.BooleanField(default=False)
    achieved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Rehabilitation Goal')
        verbose_name_plural = _('Rehabilitation Goals')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.patient}"
    
    @property
    def progress_percentage(self):
        if self.target_value == 0:
            return 0
        return min((self.current_value / self.target_value) * 100, 100)
    
    def update_progress(self, new_value):
        self.current_value = new_value
        if new_value >= self.target_value and not self.is_achieved:
            self.is_achieved = True
            from django.utils import timezone
            self.achieved_at = timezone.now()
        self.save()


class GoalProgress(models.Model):
    goal = models.ForeignKey(RehabilitationGoal, on_delete=models.CASCADE, related_name='progress_entries')
    value = models.FloatField()
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey('staff.StaffProfile', on_delete=models.CASCADE, null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Goal Progress')
        verbose_name_plural = _('Goal Progress Entries')
        ordering = ['-recorded_at']
    
    def __str__(self):
        return f"{self.goal.title} - {self.value} on {self.recorded_at.date()}"