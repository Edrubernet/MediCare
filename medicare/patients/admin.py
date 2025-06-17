from django.contrib import admin
from .models import PatientProfile, MedicalHistory, RehabilitationHistory


class MedicalHistoryInline(admin.StackedInline):
    model = MedicalHistory
    can_delete = False
    verbose_name = 'Медична історія'
    verbose_name_plural = 'Медичні історії'
    extra = 0


class RehabilitationHistoryInline(admin.TabularInline):
    model = RehabilitationHistory
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_username', 'date_of_birth', 'gender', 'get_assigned_doctors_count')
    list_filter = ('gender', 'date_of_birth')
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'user__email')
    filter_horizontal = ('assigned_doctors',)
    inlines = [MedicalHistoryInline, RehabilitationHistoryInline]
    
    fieldsets = (
        ('Особиста інформація', {
            'fields': ('user', 'date_of_birth', 'gender', 'address')
        }),
        ('Контакти екстреної допомоги', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Призначені лікарі', {
            'fields': ('assigned_doctors',)
        })
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Повне ім\'я'
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    
    def get_assigned_doctors_count(self, obj):
        return obj.assigned_doctors.count()
    get_assigned_doctors_count.short_description = 'Кількість лікарів'


@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ('patient', 'get_conditions_preview')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'conditions')
    
    def get_conditions_preview(self, obj):
        if obj.conditions:
            return obj.conditions[:100] + '...' if len(obj.conditions) > 100 else obj.conditions
        return 'Немає даних'
    get_conditions_preview.short_description = 'Стан здоров\'я'


@admin.register(RehabilitationHistory)
class RehabilitationHistoryAdmin(admin.ModelAdmin):
    list_display = ('patient', 'injury_type', 'injury_date', 'doctor', 'created_at')
    list_filter = ('injury_date', 'created_at', 'doctor')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'injury_type', 'diagnosis')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'injury_date'
