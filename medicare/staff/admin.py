from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.shortcuts import render
from .models import User, StaffProfile, Certificate, WorkSchedule


class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    can_delete = False
    verbose_name = 'Профіль персоналу'
    verbose_name_plural = 'Профілі персоналу'
    extra = 0


def create_staff_profile_for_doctors(modeladmin, request, queryset):
    """Створює StaffProfile для обраних лікарів"""
    created_count = 0
    for user in queryset:
        if user.user_type == 'doctor' and not hasattr(user, 'staff_profile'):
            StaffProfile.objects.create(
                user=user,
                specialization='Не вказано',
                bio=f'Профіль створено автоматично для {user.get_full_name()}'
            )
            created_count += 1
    
    modeladmin.message_user(request, f'Створено {created_count} профілів персоналу.')
create_staff_profile_for_doctors.short_description = "Створити профілі персоналу для лікарів"


def create_patient_profile_for_patients(modeladmin, request, queryset):
    """Створює PatientProfile для обраних пацієнтів"""
    from patients.models import PatientProfile
    created_count = 0
    for user in queryset:
        if user.user_type == 'patient' and not hasattr(user, 'patient_profile'):
            PatientProfile.objects.create(user=user)
            created_count += 1
    
    modeladmin.message_user(request, f'Створено {created_count} профілів пацієнтів.')
create_patient_profile_for_patients.short_description = "Створити профілі пацієнтів"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'patronymic', 'email', 'phone_number', 'profile_image')}),
        (_('System info'), {'fields': ('user_type',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Security'), {'fields': ('failed_login_attempts', 'account_locked_until', 'last_password_change', 'must_change_password')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'patronymic', 'user_type', 'password1', 'password2'),
        }),
    )
    list_display = ('get_full_name', 'username', 'email', 'user_type', 'is_active')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('last_name', 'first_name')
    actions = [create_staff_profile_for_doctors, create_patient_profile_for_patients]
    
    inlines = []
    
    def get_inlines(self, request, obj):
        # Додаємо StaffProfile inline тільки для лікарів та адмінів
        if obj and obj.user_type in ['doctor', 'admin']:
            return [StaffProfileInline]
        return []
    
    def get_full_name(self, obj):
        full_name = obj.get_full_name()
        if obj.patronymic:
            full_name += f" {obj.patronymic}"
        return full_name or obj.username
    get_full_name.short_description = 'Повне ім\'я'


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'get_full_name')
    list_filter = ('specialization',)
    search_fields = ('user__first_name', 'user__last_name', 'specialization')
    filter_horizontal = ('certificates',)
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Повне ім\'я'


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('name', 'issue_date')
    list_filter = ('issue_date',)
    search_fields = ('name',)
    date_hierarchy = 'issue_date'


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ('staff', 'day_of_week', 'start_time', 'end_time')
    list_filter = ('day_of_week', 'start_time')
    search_fields = ('staff__user__first_name', 'staff__user__last_name')
