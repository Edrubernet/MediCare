from django.contrib import admin
from .models import Notification, NotificationSetting, Reminder


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__first_name', 'recipient__last_name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = "Mark selected notifications as unread"


@admin.register(NotificationSetting)
class NotificationSettingAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_notifications', 'sms_notifications', 'push_notifications',
                    'message_notifications', 'appointment_reminders')
    list_filter = ('email_notifications', 'sms_notifications', 'push_notifications')
    search_fields = ('user__first_name', 'user__last_name', 'user__username')


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'scheduled_time', 'is_sent', 'created_at')
    list_filter = ('is_sent', 'scheduled_time', 'created_at')
    search_fields = ('title', 'message', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'scheduled_time'
    actions = ['mark_as_sent']
    
    def mark_as_sent(self, request, queryset):
        queryset.update(is_sent=True)
    mark_as_sent.short_description = "Mark selected reminders as sent"
