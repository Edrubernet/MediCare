"""
Безпечні views для управління пацієнтами (MPA)
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from core.permissions import (
    therapist_or_admin_required, 
    check_patient_access,
    RoleBasedQuerySetMixin
)
from .models import PatientProfile, MedicalHistory, RehabilitationHistory
from .forms import PatientProfileForm, MedicalHistoryForm, RehabilitationHistoryForm
import logging

logger = logging.getLogger('medicare.security')


class PatientQuerySetMixin(RoleBasedQuerySetMixin):
    """Міксин для безпечного доступу до даних пацієнтів"""
    
    def get_therapist_queryset(self, user, base_queryset):
        try:
            # Лікарі тепер можуть бачити всіх пацієнтів
            return base_queryset.all()
        except:
            return base_queryset.none()
    
    def get_patient_queryset(self, user, base_queryset):
        try:
            return base_queryset.filter(user=user)
        except:
            return base_queryset.none()


@therapist_or_admin_required
def patient_list(request):
    """Безпечний список пацієнтів"""
    mixin = PatientQuerySetMixin()
    patients_qs = mixin.get_user_queryset(
        request.user, 
        PatientProfile.objects.select_related('user').prefetch_related('assigned_doctors')
    )
    
    # Пошук
    search_query = request.GET.get('search', '').strip()
    if search_query:
        patients_qs = patients_qs.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(emergency_contact_name__icontains=search_query)
        )
    
    # Фільтрація "Мої пацієнти" для лікарів
    my_patients_only = request.GET.get('my_patients') == 'true'
    if my_patients_only and request.user.user_type == 'doctor':
        try:
            doctor_profile = request.user.staff_profile
            patients_qs = patients_qs.filter(assigned_doctors=doctor_profile)
        except:
            patients_qs = patients_qs.none()
    
    # Фільтрація за статтю
    gender_filter = request.GET.get('gender')
    if gender_filter and gender_filter in ['M', 'F', 'O']:
        patients_qs = patients_qs.filter(gender=gender_filter)
    
    # Сортування
    sort_by = request.GET.get('sort', 'user__last_name')
    if sort_by in ['user__last_name', 'user__first_name', 'user__date_joined', '-user__date_joined']:
        patients_qs = patients_qs.order_by(sort_by)
    
    # Пагінація
    paginator = Paginator(patients_qs, 20)
    page_number = request.GET.get('page')
    patients = paginator.get_page(page_number)
    
    # Логування доступу
    logger.info(f"User {request.user.id} accessed patient list. Query: '{search_query}'")
    
    context = {
        'patients': patients,
        'search_query': search_query,
        'gender_filter': gender_filter,
        'sort_by': sort_by,
        'my_patients_only': my_patients_only,
        'total_count': patients_qs.count(),
    }
    
    return render(request, 'patients/patient_list.html', context)


@therapist_or_admin_required
def patient_detail(request, patient_id):
    """Детальна інформація про пацієнта з перевіркою доступу"""
    patient = get_object_or_404(PatientProfile, id=patient_id)
    
    # Критична перевірка доступу
    if not check_patient_access(request.user, patient_id):
        logger.warning(
            f"Unauthorized access attempt to patient {patient_id} by user {request.user.id}"
        )
        messages.error(request, 'У вас немає доступу до даних цього пацієнта.')
        return redirect('patients:patient_list')
    
    # Отримання пов'язаних даних
    try:
        medical_history = patient.medical_history
    except MedicalHistory.DoesNotExist:
        medical_history = None
    
    rehabilitation_history = patient.rehabilitation_history.all().order_by('-created_at')[:10]
    
    # Статистика
    stats = {
        'total_rehab_records': patient.rehabilitation_history.count(),
        'assigned_doctors_count': patient.assigned_doctors.count(),
        'active_programs': patient.rehab_programs.filter(status='active').count(),
        'total_appointments': patient.appointments.count(),
    }
    
    context = {
        'patient': patient,
        'medical_history': medical_history,
        'rehabilitation_history': rehabilitation_history,
        'stats': stats,
    }
    
    return render(request, 'patients/patient_detail.html', context)


@therapist_or_admin_required
@require_http_methods(["GET", "POST"])
def patient_edit(request, patient_id):
    """Редагування профілю пацієнта"""
    patient = get_object_or_404(PatientProfile, id=patient_id)
    
    # Перевірка доступу
    if not check_patient_access(request.user, patient_id):
        logger.warning(
            f"Unauthorized edit attempt for patient {patient_id} by user {request.user.id}"
        )
        messages.error(request, 'У вас немає дозволу редагувати цього пацієнта.')
        return redirect('patients:patient_detail', patient_id=patient_id)
    
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            logger.info(f"Patient {patient_id} updated by user {request.user.id}")
            messages.success(request, 'Профіль пацієнта успішно оновлено.')
            return redirect('patients:patient_detail', patient_id=patient_id)
    else:
        form = PatientProfileForm(instance=patient)
    
    context = {
        'form': form,
        'patient': patient,
    }
    
    return render(request, 'patients/patient_edit.html', context)


@therapist_or_admin_required
@require_http_methods(["GET", "POST"])
def medical_history_edit(request, patient_id):
    """Редагування медичної історії"""
    patient = get_object_or_404(PatientProfile, id=patient_id)
    
    # Перевірка доступу
    if not check_patient_access(request.user, patient_id):
        messages.error(request, 'У вас немає доступу до медичних даних цього пацієнта.')
        return redirect('patients:patient_detail', patient_id=patient_id)
    
    try:
        medical_history = patient.medical_history
    except MedicalHistory.DoesNotExist:
        medical_history = None
    
    if request.method == 'POST':
        form = MedicalHistoryForm(request.POST, instance=medical_history)
        if form.is_valid():
            history = form.save(commit=False)
            if not medical_history:  # Створення нової історії
                history.patient = patient
            history.save()
            
            logger.info(f"Medical history for patient {patient_id} updated by user {request.user.id}")
            messages.success(request, 'Медичну історію успішно оновлено.')
            return redirect('patients:patient_detail', patient_id=patient_id)
    else:
        form = MedicalHistoryForm(instance=medical_history)
    
    context = {
        'form': form,
        'patient': patient,
        'medical_history': medical_history,
    }
    
    return render(request, 'patients/medical_history_edit.html', context)


@therapist_or_admin_required
@require_http_methods(["GET", "POST"])
def add_rehabilitation_record(request, patient_id):
    """Додавання запису реабілітації"""
    patient = get_object_or_404(PatientProfile, id=patient_id)
    
    # Перевірка доступу
    if not check_patient_access(request.user, patient_id):
        messages.error(request, 'У вас немає дозволу додавати записи для цього пацієнта.')
        return redirect('patients:patient_detail', patient_id=patient_id)
    
    if request.method == 'POST':
        form = RehabilitationHistoryForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.patient = patient
            
            # Автоматично призначаємо лікаря, якщо це не адміністратор
            if request.user.user_type == 'doctor':
                try:
                    record.doctor = request.user.staff_profile
                except:
                    pass
            
            record.save()
            
            logger.info(f"Rehabilitation record added for patient {patient_id} by user {request.user.id}")
            messages.success(request, 'Запис реабілітації успішно додано.')
            return redirect('patients:patient_detail', patient_id=patient_id)
    else:
        form = RehabilitationHistoryForm()
    
    context = {
        'form': form,
        'patient': patient,
    }
    
    return render(request, 'patients/add_rehabilitation_record.html', context)


@therapist_or_admin_required
def rehabilitation_record_detail(request, patient_id, record_id):
    """Детальний перегляд запису реабілітації"""
    patient = get_object_or_404(PatientProfile, id=patient_id)
    record = get_object_or_404(RehabilitationHistory, id=record_id, patient=patient)
    
    # Перевірка доступу
    if not check_patient_access(request.user, patient_id):
        messages.error(request, 'У вас немає доступу до даних цього пацієнта.')
        return redirect('patients:patient_list')
    
    context = {
        'patient': patient,
        'record': record,
    }
    
    return render(request, 'patients/rehabilitation_record_detail.html', context)


@therapist_or_admin_required
def assign_doctor(request, patient_id):
    """AJAX endpoint для призначення лікаря пацієнту"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не дозволений'}, status=405)
    
    patient = get_object_or_404(PatientProfile, id=patient_id)
    
    # Тільки адміністратори можуть призначати лікарів
    if request.user.user_type != 'admin':
        logger.warning(f"Non-admin user {request.user.id} tried to assign doctor")
        return JsonResponse({'error': 'Недостатньо прав'}, status=403)
    
    doctor_id = request.POST.get('doctor_id')
    if not doctor_id:
        return JsonResponse({'error': 'doctor_id обов\'язкове поле'}, status=400)
    
    try:
        from staff.models import StaffProfile
        doctor = StaffProfile.objects.get(id=doctor_id, user__user_type='doctor')
        
        if doctor in patient.assigned_doctors.all():
            return JsonResponse({'error': 'Лікар уже призначений цьому пацієнту'}, status=400)
        
        patient.assigned_doctors.add(doctor)
        
        logger.info(f"Doctor {doctor_id} assigned to patient {patient_id} by admin {request.user.id}")
        
        return JsonResponse({
            'success': True,
            'message': f'Лікар {doctor.user.get_full_name()} успішно призначений'
        })
        
    except StaffProfile.DoesNotExist:
        return JsonResponse({'error': 'Лікар не знайдений'}, status=404)
    except Exception as e:
        logger.error(f"Error assigning doctor: {str(e)}")
        return JsonResponse({'error': 'Внутрішня помилка сервера'}, status=500)


@login_required
def my_profile(request):
    """Профіль для пацієнтів - можуть бачити тільки свої дані"""
    if request.user.user_type != 'patient':
        messages.error(request, 'Цей розділ доступний тільки для пацієнтів.')
        return redirect('core:dashboard')
    
    try:
        patient = request.user.patient_profile
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Профіль пацієнта не знайдено.')
        return redirect('core:home')
    
    # Медична історія
    try:
        medical_history = patient.medical_history
    except MedicalHistory.DoesNotExist:
        medical_history = None
    
    # Останні записи реабілітації
    recent_records = patient.rehabilitation_history.all().order_by('-created_at')[:5]
    
    context = {
        'patient': patient,
        'medical_history': medical_history,
        'recent_records': recent_records,
        'assigned_doctors': patient.assigned_doctors.all(),
    }
    
    return render(request, 'patients/my_profile.html', context)


# ==================== API VIEWS ====================

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json


@method_decorator(csrf_exempt, name='dispatch')
class PatientSearchAPIView(View):
    """
    API view для пошуку пацієнтів (для лікарів)
    """
    
    def get(self, request):
        # Перевірка аутентифікації
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Перевірка ролі лікаря
        if request.user.user_type != 'doctor':
            return JsonResponse({'error': 'Only doctors can search patients'}, status=403)
        
        # Отримання пошукового запиту
        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse([], safe=False)
        
        try:
            # Отримання профілю лікаря
            doctor_profile = request.user.staff_profile
            assigned_patient_ids = doctor_profile.patients.values_list('user_id', flat=True)
        except AttributeError:
            return JsonResponse([], safe=False)
        
        # Пошук користувачів-пацієнтів
        from staff.models import User
        patients = User.objects.filter(
            user_type='patient'
        ).filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).exclude(
            id__in=assigned_patient_ids
        ).select_related('patient_profile')[:10]
        
        # Формування результату
        results = []
        for patient in patients:
            try:
                results.append({
                    'id': patient.id,
                    'profile_id': patient.patient_profile.id,
                    'full_name': patient.get_full_name(),
                    'email': patient.email
                })
            except:
                continue
        
        return JsonResponse(results, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class PatientProfilesAPIView(View):
    """
    API view для отримання списку пацієнтів лікаря
    """
    
    def get(self, request):
        # Перевірка аутентифікації
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Отримання параметрів
        page = int(request.GET.get('page', 1))
        search = request.GET.get('search', '').strip()
        ordering = request.GET.get('ordering', 'user__last_name')
        
        # Базовий QuerySet в залежності від ролі
        if request.user.user_type == 'admin':
            patients_qs = PatientProfile.objects.all()
        elif request.user.user_type == 'doctor':
            try:
                doctor_profile = request.user.staff_profile
                patients_qs = PatientProfile.objects.filter(assigned_doctors=doctor_profile)
            except AttributeError:
                return JsonResponse({'results': [], 'count': 0}, safe=False)
        else:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Пошук
        if search:
            patients_qs = patients_qs.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search)
            )
        
        # Сортування
        valid_ordering = ['user__last_name', 'user__first_name', '-user__date_joined', 'user__date_joined']
        if ordering in valid_ordering:
            patients_qs = patients_qs.order_by(ordering)
        else:
            patients_qs = patients_qs.order_by('user__last_name')
        
        # Пагінація
        total_count = patients_qs.count()
        per_page = 20
        start = (page - 1) * per_page
        end = start + per_page
        patients = patients_qs.select_related('user')[start:end]
        
        # Формування результату
        results = []
        for patient in patients:
            results.append({
                'id': patient.id,
                'user': {
                    'id': patient.user.id,
                    'full_name': patient.user.get_full_name(),
                    'email': patient.user.email,
                    'date_joined': patient.user.date_joined.isoformat(),
                    'avatar': None  # Додати аватар якщо є
                },
                'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                'gender': patient.gender,
                'medical_history': None  # Спрощено для початку
            })
        
        return JsonResponse({
            'results': results,
            'count': total_count,
            'page': page,
            'per_page': per_page
        })


@csrf_exempt
def assign_patient_to_doctor_api(request, patient_id):
    """
    API endpoint для призначення пацієнта лікарю
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.user.user_type != 'doctor':
        return JsonResponse({'error': 'Only doctors can assign patients'}, status=403)
    
    try:
        patient = PatientProfile.objects.get(id=patient_id)
        doctor_profile = request.user.staff_profile
        
        # Перевіряємо чи пацієнт вже призначений
        if doctor_profile in patient.assigned_doctors.all():
            return JsonResponse({'error': 'Patient already assigned'}, status=400)
        
        # Призначаємо пацієнта
        patient.assigned_doctors.add(doctor_profile)
        
        logger.info(f"Patient {patient_id} assigned to doctor {request.user.id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Patient successfully assigned'
        })
        
    except PatientProfile.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)
    except Exception as e:
        logger.error(f"Error assigning patient: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
@require_http_methods(["POST"])
def toggle_patient_assignment(request, patient_id):
    """Toggle призначення пацієнта поточному лікарю"""
    if request.user.user_type != 'doctor':
        return JsonResponse({'success': False, 'error': 'Тільки лікарі можуть призначати пацієнтів'})
    
    try:
        patient = get_object_or_404(PatientProfile, id=patient_id)
        doctor_profile = request.user.staff_profile
        
        # Отримуємо дію з JSON body
        import json
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'add':
            if doctor_profile in patient.assigned_doctors.all():
                return JsonResponse({'success': False, 'error': 'Пацієнт вже призначений'})
            
            patient.assigned_doctors.add(doctor_profile)
            
            # Створення notification для пацієнта
            from notification.models import Notification
            Notification.objects.create(
                recipient=patient.user,
                notification_type='assignment',
                title='Новий лікар призначений',
                message=f'Лікар {doctor_profile.user.get_full_name()} був призначений для вашого лікування'
            )
            
            logger.info(f"Patient {patient_id} assigned to doctor {request.user.id}")
            return JsonResponse({'success': True, 'message': 'Пацієнт успішно призначений'})
            
        elif action == 'remove':
            if doctor_profile not in patient.assigned_doctors.all():
                return JsonResponse({'success': False, 'error': 'Пацієнт не призначений'})
            
            patient.assigned_doctors.remove(doctor_profile)
            
            # Створення notification для пацієнта
            from notification.models import Notification
            Notification.objects.create(
                recipient=patient.user,
                notification_type='assignment',
                title='Призначення лікаря відмінено',
                message=f'Лікар {doctor_profile.user.get_full_name()} більше не веде ваше лікування'
            )
            
            logger.info(f"Patient {patient_id} unassigned from doctor {request.user.id}")
            return JsonResponse({'success': True, 'message': 'Призначення пацієнта відмінено'})
            
        else:
            return JsonResponse({'success': False, 'error': 'Невірна дія'})
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неправильний формат даних'})
    except Exception as e:
        logger.error(f"Error toggling patient assignment: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Помилка сервера'})