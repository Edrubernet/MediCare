"""
Моделі для системи програм реабілітації
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class RehabilitationProgram(models.Model):
    """Програма реабілітації"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('completed', _('Completed')),
        ('paused', _('Paused')),
        ('cancelled', _('Cancelled')),
    ]
    
    title = models.CharField(max_length=255, verbose_name=_('Program Title'))
    description = models.TextField(verbose_name=_('Description'))
    patient = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE, 
                               related_name='rehab_programs')
    doctor = models.ForeignKey('staff.StaffProfile', on_delete=models.CASCADE,
                              related_name='assigned_programs')
    
    # Параметри програми
    start_date = models.DateField(verbose_name=_('Start Date'))
    end_date = models.DateField(blank=True, null=True, verbose_name=_('End Date'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Цілі та очікувані результати
    goals = models.TextField(blank=True, null=True, verbose_name=_('Goals'))
    expected_outcomes = models.TextField(blank=True, null=True, verbose_name=_('Expected Outcomes'))
    
    # Частота занять
    sessions_per_week = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        verbose_name=_('Sessions per Week')
    )
    session_duration = models.PositiveIntegerField(
        default=60,
        help_text=_('Duration in minutes'),
        verbose_name=_('Session Duration')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Rehabilitation Program')
        verbose_name_plural = _('Rehabilitation Programs')
        ordering = ['-created_at']
        permissions = [
            ('can_assign_program', 'Can assign rehabilitation program'),
            ('can_modify_program', 'Can modify rehabilitation program'),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.patient}"
    
    @property
    def is_active(self):
        return (self.status == 'active' and 
                self.start_date <= timezone.now().date() and
                (not self.end_date or self.end_date >= timezone.now().date()))
    
    @property
    def progress_percentage(self):
        if self.status == 'completed':
            return 100
        if not self.end_date:
            return 0
        total_days = (self.end_date - self.start_date).days
        if total_days <= 0:
            return 0
        elapsed_days = (timezone.now().date() - self.start_date).days
        return min(max(int((elapsed_days / total_days) * 100), 0), 100)


class ProgramDay(models.Model):
    """День програми реабілітації"""
    program = models.ForeignKey(RehabilitationProgram, on_delete=models.CASCADE, 
                               related_name='program_days')
    day_number = models.PositiveIntegerField(verbose_name=_('Day Number'))
    notes = models.TextField(blank=True, null=True, verbose_name=_('Notes'))
    
    class Meta:
        verbose_name = _('Program Day')
        verbose_name_plural = _('Program Days')
        ordering = ['day_number']
        unique_together = ('program', 'day_number')
    
    def __str__(self):
        return f"{self.program.title} - Day {self.day_number}"


class ProgramExercise(models.Model):
    """Вправа в програмі реабілітації"""
    program_day = models.ForeignKey(ProgramDay, on_delete=models.CASCADE, 
                                   related_name='exercises')
    exercise = models.ForeignKey('exercises.Exercise', on_delete=models.CASCADE,
                                related_name='program_exercises')
    
    # Параметри виконання
    sets = models.PositiveIntegerField(default=1, verbose_name=_('Sets'))
    repetitions = models.PositiveIntegerField(default=10, verbose_name=_('Repetitions'))
    duration = models.PositiveIntegerField(
        blank=True, null=True, 
        help_text=_('Duration in seconds, if applicable'),
        verbose_name=_('Duration (seconds)')
    )
    rest_between_sets = models.PositiveIntegerField(
        default=60,
        help_text=_('Rest time in seconds'),
        verbose_name=_('Rest between sets (seconds)')
    )
    
    # Порядок та інструкції
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    additional_instructions = models.TextField(
        blank=True, null=True,
        verbose_name=_('Additional Instructions')
    )
    
    # Дні тижня для виконання (JSON поле)
    days_of_week = models.JSONField(
        default=list, 
        help_text=_('List of weekday numbers (0=Monday)'),
        blank=True
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Program Exercise')
        verbose_name_plural = _('Program Exercises')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.exercise.title} - {self.sets}x{self.repetitions}"


class Appointment(models.Model):
    """Запис на прийом"""
    APPOINTMENT_STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('confirmed', _('Confirmed')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
    ]
    
    APPOINTMENT_TYPE_CHOICES = [
        ('consultation', _('Consultation')),
        ('therapy_session', _('Therapy Session')),
        ('assessment', _('Assessment')),
        ('follow_up', _('Follow-up')),
    ]
    
    patient = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE,
                               related_name='appointments')
    doctor = models.ForeignKey('staff.StaffProfile', on_delete=models.CASCADE,
                              related_name='appointments')
    
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES,
                                       default='therapy_session')
    
    # Час та дата
    date = models.DateField(verbose_name=_('Date'))
    start_time = models.TimeField(verbose_name=_('Start Time'))
    end_time = models.TimeField(verbose_name=_('End Time'))
    
    status = models.CharField(max_length=20, choices=APPOINTMENT_STATUS_CHOICES,
                             default='scheduled')
    
    # Опис та примітки
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    notes = models.TextField(blank=True, null=True, verbose_name=_('Notes'))
    
    # Зв'язок з програмою реабілітації
    related_program = models.ForeignKey(RehabilitationProgram, on_delete=models.SET_NULL,
                                       null=True, blank=True,
                                       related_name='appointments')
    
    # Нагадування
    reminder_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Appointment')
        verbose_name_plural = _('Appointments')
        ordering = ['date', 'start_time']
        unique_together = ['doctor', 'date', 'start_time']
    
    def __str__(self):
        return f"{self.patient} - {self.doctor} ({self.date} {self.start_time})"
    
    @property
    def duration_minutes(self):
        """Тривалість прийому в хвилинах"""
        from datetime import datetime, timedelta
        start_dt = datetime.combine(self.date, self.start_time)
        end_dt = datetime.combine(self.date, self.end_time)
        return int((end_dt - start_dt).total_seconds() / 60)


class ProgressLog(models.Model):
    """Журнал прогресу пацієнта"""
    PROGRESS_TYPE_CHOICES = [
        ('exercise', _('Exercise Performance')),
        ('pain_level', _('Pain Level')),
        ('mobility', _('Mobility Assessment')),
        ('general', _('General Progress')),
        ('appointment', _('Appointment Summary')),
    ]
    
    patient = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE,
                               related_name='progress_logs')
    doctor = models.ForeignKey('staff.StaffProfile', on_delete=models.CASCADE,
                              related_name='progress_logs')
    
    progress_type = models.CharField(max_length=20, choices=PROGRESS_TYPE_CHOICES,
                                    default='general')
    
    # Дата та час запису
    log_date = models.DateTimeField(default=timezone.now)
    
    # Основний зміст
    notes = models.TextField(verbose_name=_('Progress Notes'))
    
    # Числові показники
    pain_level = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name=_('Pain Level (0-10)')
    )
    
    mobility_score = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Mobility Score (%)')
    )
    
    # Зв'язки
    related_exercise = models.ForeignKey('exercises.Exercise', on_delete=models.SET_NULL,
                                        null=True, blank=True,
                                        related_name='progress_logs')
    related_appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL,
                                           null=True, blank=True,
                                           related_name='progress_logs')
    related_program = models.ForeignKey(RehabilitationProgram, on_delete=models.SET_NULL,
                                       null=True, blank=True,
                                       related_name='progress_logs')
    
    # Медіафайли (фото, відео прогресу)
    media_files = models.JSONField(default=list, blank=True,
                                  help_text=_('List of media file paths'))
    
    # Рекомендації та подальші дії
    recommendations = models.TextField(blank=True, null=True,
                                     verbose_name=_('Recommendations'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Progress Log')
        verbose_name_plural = _('Progress Logs')
        ordering = ['-log_date']
    
    def __str__(self):
        return f"{self.patient} - {self.get_progress_type_display()} ({self.log_date.date()})"


class ExercisePerformance(models.Model):
    """Результати виконання вправ"""
    patient = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE,
                               related_name='exercise_performances')
    exercise = models.ForeignKey('exercises.Exercise', on_delete=models.CASCADE,
                                related_name='performances')
    program_exercise = models.ForeignKey(ProgramExercise, on_delete=models.SET_NULL,
                                        null=True, blank=True,
                                        related_name='performances')
    
    # Дата виконання
    performed_date = models.DateTimeField(default=timezone.now)
    
    # Фактичні параметри виконання
    completed_sets = models.PositiveIntegerField(default=0)
    completed_repetitions = models.PositiveIntegerField(default=0)
    actual_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    
    # Оцінка складності та якості виконання
    difficulty_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('1=Very Easy, 5=Very Hard'),
        verbose_name=_('Difficulty Rating')
    )
    
    quality_rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('1=Poor, 5=Excellent'),
        verbose_name=_('Quality Rating')
    )
    
    # Симптоми та побічні ефекти
    pain_before = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name=_('Pain Before (0-10)')
    )
    pain_after = models.PositiveIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name=_('Pain After (0-10)')
    )
    
    # Примітки пацієнта
    patient_notes = models.TextField(blank=True, null=True,
                                    verbose_name=_('Patient Notes'))
    
    # Чи було виконано повністю
    completed_fully = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Exercise Performance')
        verbose_name_plural = _('Exercise Performances')
        ordering = ['-performed_date']
    
    def __str__(self):
        return f"{self.patient} - {self.exercise.title} ({self.performed_date.date()})"
    
    @property
    def completion_percentage(self):
        """Відсоток виконання відносно запланованого"""
        if not self.program_exercise:
            return 100 if self.completed_fully else 0
        
        planned_sets = self.program_exercise.sets
        planned_reps = self.program_exercise.repetitions
        
        if planned_sets == 0 or planned_reps == 0:
            return 100 if self.completed_fully else 0
        
        actual_total = self.completed_sets * self.completed_repetitions
        planned_total = planned_sets * planned_reps
        
        return min(int((actual_total / planned_total) * 100), 100)