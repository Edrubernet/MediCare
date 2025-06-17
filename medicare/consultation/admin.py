from django.contrib import admin
from .models import Consultation, ConsultationNote, ConsultationRecording


class ConsultationNoteInline(admin.StackedInline):
    model = ConsultationNote
    can_delete = False
    extra = 0


class ConsultationRecordingInline(admin.StackedInline):
    model = ConsultationRecording
    can_delete = False
    extra = 0
    readonly_fields = ('duration', 'created_at')


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'start_time', 'end_time', 'status', 'consultation_type')
    list_filter = ('status', 'consultation_type', 'start_time', 'created_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 
                     'doctor__user__first_name', 'doctor__user__last_name')
    inlines = [ConsultationNoteInline, ConsultationRecordingInline]
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Consultation Details', {
            'fields': ('patient', 'doctor', 'start_time', 'end_time', 'status')
        }),
        ('Type & Access', {
            'fields': ('consultation_type', 'video_link')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ConsultationNote)
class ConsultationNoteAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('consultation__patient__user__first_name', 
                     'consultation__patient__user__last_name', 'content')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ConsultationRecording)
class ConsultationRecordingAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'duration', 'file', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('consultation__patient__user__first_name', 
                     'consultation__patient__user__last_name')
    readonly_fields = ('duration', 'created_at')
