"""
Система ролей та дозволів для центру реабілітації
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
import logging

logger = logging.getLogger('medicare.security')


def role_required(*allowed_roles):
    """
    Декоратор для перевірки ролі користувача
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.user_type in allowed_roles:
                try:
                    logger.warning(
                        f"Unauthorized access attempt by user {request.user.id} "
                        f"({request.user.user_type}) to {view_func.__name__}"
                    )
                except UnicodeEncodeError:
                    # Падбек для Windows консолі
                    logger.warning(
                        f"Unauthorized access attempt by user {request.user.id} "
                        f"(role: {request.user.user_type}) to function {view_func.__name__}"
                    )
                messages.error(request, "У вас немає дозволу для доступу до цієї сторінки.")
                # Перенаправляємо на правильний дашборд залежно від ролі
                if request.user.user_type == 'admin':
                    return redirect('core:admin_dashboard')
                elif request.user.user_type == 'doctor':
                    return redirect('core:therapist_dashboard')
                elif request.user.user_type == 'patient':
                    return redirect('core:patient_dashboard')
                else:
                    return redirect('core:home')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def patient_required(view_func):
    """Декоратор для доступу тільки пацієнтів"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type != 'patient':
            try:
                logger.warning(
                    f"Non-patient user {request.user.id} "
                    f"({request.user.user_type}) tried to access patient area"
                )
            except UnicodeEncodeError:
                logger.warning(
                    f"Non-patient user {request.user.id} tried to access patient area"
                )
            messages.error(request, "Цей розділ доступний тільки для пацієнтів.")
            # Перенаправляємо на правильний дашборд залежно від ролі
            if request.user.user_type == 'admin':
                return redirect('core:admin_dashboard')
            elif request.user.user_type == 'doctor':
                return redirect('core:therapist_dashboard')
            else:
                return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def therapist_required(view_func):
    """Декоратор для доступу тільки терапевтів"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type != 'doctor':
            messages.error(request, "Цей розділ доступний тільки для терапевтів.")
            if request.user.user_type == 'admin':
                return redirect('core:admin_dashboard')
            elif request.user.user_type == 'patient':
                return redirect('core:patient_dashboard')
            else:
                return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    """Декоратор для доступу тільки адміністраторів"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type != 'admin':
            messages.error(request, "Цей розділ доступний тільки для адміністраторів.")
            if request.user.user_type == 'doctor':
                return redirect('core:therapist_dashboard')
            elif request.user.user_type == 'patient':
                return redirect('core:patient_dashboard')
            else:
                return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def therapist_or_admin_required(view_func):
    """Декоратор для доступу терапевтів або адміністраторів"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_type not in ['doctor', 'admin']:
            messages.error(request, "Цей розділ доступний тільки для терапевтів та адміністраторів.")
            if request.user.user_type == 'patient':
                return redirect('core:patient_dashboard')
            else:
                return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


class RoleBasedQuerySetMixin:
    """
    Міксин для безпечного отримання QuerySet залежно від ролі користувача
    """
    
    def get_user_queryset(self, user, base_queryset):
        """
        Повертає безпечний QuerySet залежно від ролі користувача
        """
        if user.user_type == 'admin':
            return base_queryset
        elif user.user_type == 'doctor':
            return self.get_therapist_queryset(user, base_queryset)
        elif user.user_type == 'patient':
            return self.get_patient_queryset(user, base_queryset)
        else:
            return base_queryset.none()
    
    def get_therapist_queryset(self, user, base_queryset):
        """Переризначити в дочірніх класах"""
        return base_queryset.none()
    
    def get_patient_queryset(self, user, base_queryset):
        """Переризначити в дочірніх класах"""
        return base_queryset.none()


def check_patient_access(user, patient_id):
    """
    Перевіряє чи має користувач доступ до даних пацієнта
    """
    if user.user_type == 'admin':
        return True
    elif user.user_type == 'doctor':
        try:
            from patients.models import PatientProfile
            patient = PatientProfile.objects.get(id=patient_id)
            return patient.assigned_doctors.filter(user=user).exists()
        except PatientProfile.DoesNotExist:
            return False
    elif user.user_type == 'patient':
        try:
            from patients.models import PatientProfile
            patient = PatientProfile.objects.get(id=patient_id)
            return patient.user == user
        except PatientProfile.DoesNotExist:
            return False
    return False


def check_data_access(user, model_instance):
    """
    Універсальна перевірка доступу до медичних даних
    """
    if user.user_type == 'admin':
        return True
    
    # Отримуємо пацієнта з різних типів моделей
    patient = None
    if hasattr(model_instance, 'patient'):
        patient = model_instance.patient
    elif hasattr(model_instance, 'user') and hasattr(model_instance.user, 'patient_profile'):
        patient = model_instance.user.patient_profile
    
    if not patient:
        return False
    
    return check_patient_access(user, patient.id)