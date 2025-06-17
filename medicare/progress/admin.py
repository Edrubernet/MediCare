from django.contrib import admin
from .models import ExerciseSession, ExerciseCompletion, PatientNote


class ExerciseCompletionInline(admin.TabularInline):
    model = ExerciseCompletion
    extra = 0
    readonly_fields = ('completed_at',)


@admin.register(ExerciseSession)
class ExerciseSessionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'program', 'date', 'completed', 'created_at')
    list_filter = ('completed', 'date', 'created_at')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'program__name')
    inlines = [ExerciseCompletionInline]
    readonly_fields = ('created_at',)
    date_hierarchy = 'date'


@admin.register(ExerciseCompletion)
class ExerciseCompletionAdmin(admin.ModelAdmin):
    list_display = ('get_patient', 'get_exercise', 'sets_completed', 'repetitions_completed', 
                    'pain_level', 'difficulty_level', 'completed_at')
    list_filter = ('pain_level', 'difficulty_level', 'completed_at')
    search_fields = ('session__patient__user__first_name', 'session__patient__user__last_name',
                     'program_exercise__exercise__title')
    readonly_fields = ('completed_at',)
    date_hierarchy = 'completed_at'
    
    def get_patient(self, obj):
        return obj.session.patient
    get_patient.short_description = 'Patient'
    
    def get_exercise(self, obj):
        return obj.program_exercise.exercise.title
    get_exercise.short_description = 'Exercise'



@admin.register(PatientNote)
class PatientNoteAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'get_note_preview', 'created_at')
    list_filter = ('created_at', 'doctor')
    search_fields = ('patient__user__first_name', 'patient__user__last_name',
                     'doctor__user__first_name', 'doctor__user__last_name', 'note')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def get_note_preview(self, obj):
        return obj.note[:100] + '...' if len(obj.note) > 100 else obj.note
    get_note_preview.short_description = 'Note Preview'
