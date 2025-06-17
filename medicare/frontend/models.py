from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class UserPreference(models.Model):
    """User interface preferences and settings"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='ui_preferences'
    )
    theme = models.CharField(
        max_length=20, 
        choices=[
            ('light', _('Light Theme')),
            ('dark', _('Dark Theme')),
            ('auto', _('Auto (System)')),
        ],
        default='light'
    )
    language = models.CharField(
        max_length=10,
        choices=[
            ('uk', _('Ukrainian')),
            ('en', _('English')),
        ],
        default='uk'
    )
    notifications_enabled = models.BooleanField(default=True)
    dashboard_layout = models.CharField(
        max_length=20,
        choices=[
            ('compact', _('Compact')),
            ('comfortable', _('Comfortable')),
            ('spacious', _('Spacious')),
        ],
        default='comfortable'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('User Preference')
        verbose_name_plural = _('User Preferences')

    def __str__(self):
        return f"Preferences for {self.user.get_full_name()}"


class DashboardWidget(models.Model):
    """Dashboard widget configuration"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_widgets'
    )
    widget_type = models.CharField(
        max_length=50,
        choices=[
            ('appointments', _('Upcoming Appointments')),
            ('progress', _('Progress Overview')),
            ('exercises', _('Exercise Schedule')),
            ('notifications', _('Recent Notifications')),
            ('statistics', _('Statistics')),
            ('quick_actions', _('Quick Actions')),
        ]
    )
    position = models.PositiveSmallIntegerField(default=0)
    is_enabled = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = _('Dashboard Widget')
        verbose_name_plural = _('Dashboard Widgets')
        ordering = ['position']
        unique_together = ['user', 'widget_type']

    def __str__(self):
        return f"{self.user.username} - {self.get_widget_type_display()}"
