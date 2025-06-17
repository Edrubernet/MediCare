from django.contrib import admin
from .models import UserPreference, DashboardWidget


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'theme', 'language', 'notifications_enabled', 'dashboard_layout', 'updated_at')
    list_filter = ('theme', 'language', 'notifications_enabled', 'dashboard_layout')
    search_fields = ('user__first_name', 'user__last_name', 'user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'widget_type', 'position', 'is_enabled')
    list_filter = ('widget_type', 'is_enabled')
    search_fields = ('user__first_name', 'user__last_name', 'user__username')
    list_editable = ('position', 'is_enabled')
    ordering = ('user', 'position')
