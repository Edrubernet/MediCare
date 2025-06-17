from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Report(models.Model):
    REPORT_TYPES = (
        ('patient_progress', _('Patient Progress')),
        ('program_completion', _('Program Completion')),
        ('doctor_activity', _('Doctor Activity')),
        ('survey_results', _('Survey Results')),
        ('system_usage', _('System Usage')),
        ('custom', _('Custom Report')),
    )

    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True, null=True)
    parameters = models.JSONField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_reports')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Report')
        verbose_name_plural = _('Reports')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"


class ReportExport(models.Model):
    EXPORT_FORMATS = (
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel'),
    )

    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='exports')
    file = models.FileField(upload_to='report_exports/')
    format = models.CharField(max_length=10, choices=EXPORT_FORMATS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Report Export')
        verbose_name_plural = _('Report Exports')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.report.title} - {self.format}"