from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Survey(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_surveys')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Survey')
        verbose_name_plural = _('Surveys')
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = (
        ('text', _('Text Answer')),
        ('single_choice', _('Single Choice')),
        ('multiple_choice', _('Multiple Choice')),
        ('rating', _('Rating (1-10)')),
        ('yes_no', _('Yes/No')),
    )

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')
        ordering = ['order']

    def __str__(self):
        return f"{self.text} ({self.get_question_type_display()})"


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = _('Question Option')
        verbose_name_plural = _('Question Options')
        ordering = ['order']

    def __str__(self):
        return self.text


class SurveyAssignment(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('completed', _('Completed')),
        ('expired', _('Expired')),
    )

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='assignments')
    patient = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE, related_name='survey_assignments')
    assigned_by = models.ForeignKey('staff.StaffProfile', on_delete=models.CASCADE, related_name='assigned_surveys')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField(blank=True, null=True)
    assigned_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('Survey Assignment')
        verbose_name_plural = _('Survey Assignments')
        ordering = ['-assigned_date']

    def __str__(self):
        return f"{self.survey.title} - {self.patient}"


class SurveyResponse(models.Model):
    assignment = models.OneToOneField(SurveyAssignment, on_delete=models.CASCADE, related_name='response')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = _('Survey Response')
        verbose_name_plural = _('Survey Responses')

    def __str__(self):
        return f"Response for {self.assignment}"


class QuestionResponse(models.Model):
    survey_response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, related_name='question_responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text_answer = models.TextField(blank=True, null=True)
    selected_options = models.ManyToManyField(QuestionOption, blank=True, related_name='responses')
    rating_answer = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = _('Question Response')
        verbose_name_plural = _('Question Responses')

    def __str__(self):
        return f"Response to {self.question.text}"