"""
Основні views для MPA системи
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count
from datetime import datetime, timedelta

from .permissions import (
    role_required, patient_required, therapist_required, admin_required,
    therapist_or_admin_required, check_patient_access
)
from staff.models import User, StaffProfile
from patients.models import PatientProfile, MedicalHistory, RehabilitationHistory
from programs.models import RehabilitationProgram
from consultation.models import Consultation
from progress.models import ExerciseSession, PatientNote


def home(request):
    """Головна сторінка"""
    if request.user.is_authenticated:
        # Перевіряємо чи є user_type у користувача
        if hasattr(request.user, 'user_type') and request.user.user_type:
            if request.user.user_type == 'admin':
                return redirect('core:admin_dashboard')
            elif request.user.user_type == 'doctor':
                return redirect('core:therapist_dashboard')
            elif request.user.user_type == 'patient':
                return redirect('core:patient_dashboard')
        # Якщо немає user_type або він порожній - виходимо з системи
        logout(request)
        messages.warning(request, 'Невизначена роль користувача. Будь ласка, увійдіть знову.')
    return render(request, 'core/home.html')


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Безпечний вхід в систему"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Будь ласка, заповніть всі поля.')
            return render(request, 'core/login.html')
        
        # Перевірка блокування аккаунту
        try:
            user = User.objects.get(username=username)
            if (user.account_locked_until and 
                user.account_locked_until > timezone.now()):
                messages.error(request, 'Аккаунт тимчасово заблокований. Спробуйте пізніше.')
                return render(request, 'core/login.html')
        except User.DoesNotExist:
            pass
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Успішний вхід - скидаємо лічильник невдалих спроб
            user.failed_login_attempts = 0
            user.account_locked_until = None
            user.save(update_fields=['failed_login_attempts', 'account_locked_until'])
            
            login(request, user)
            messages.success(request, f'Ласкаво просимо, {user.get_full_name()}!')
            
            # Перенаправлення на відповідний дашборд
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('core:dashboard')
        else:
            # Невдалий вхід - збільшуємо лічильник
            try:
                user = User.objects.get(username=username)
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.account_locked_until = timezone.now() + timedelta(minutes=30)
                    messages.error(request, 'Занадто багато невдалих спроб. Аккаунт заблокований на 30 хвилин.')
                else:
                    messages.error(request, f'Невірні дані для входу. Залишилось спроб: {5 - user.failed_login_attempts}')
                user.save(update_fields=['failed_login_attempts', 'account_locked_until'])
            except User.DoesNotExist:
                messages.error(request, 'Невірні дані для входу.')
    
    return render(request, 'core/login.html')


@login_required
def logout_view(request):
    """Вихід з системи"""
    logout(request)
    messages.info(request, 'Ви успішно вийшли з системи.')
    return redirect('core:home')


def force_logout(request):
    """Примусовий вихід з очищенням сесії"""
    logout(request)
    request.session.flush()
    messages.warning(request, 'Сесію очищено. Будь ласка, увійдіть знову.')
    return redirect('core:home')


@login_required
def dashboard(request):
    """Головний дашборд з перенаправленням на роль-специфічні дашборди"""
    # Перенаправляємо на головну сторінку, яка вже має логіку роутингу
    return redirect('core:home')


def admin_dashboard(request):
    """Дашборд адміністратора"""
    # Перевіряємо авторизацію та роль вручну
    if not request.user.is_authenticated:
        return redirect('core:login')
    
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'admin':
        messages.error(request, 'Доступ заборонено. Тільки для адміністраторів.')
        logout(request)
        return redirect('core:home')
    # Статистика системи
    stats = {
        'total_users': User.objects.count(),
        'total_patients': PatientProfile.objects.count(),
        'total_therapists': User.objects.filter(user_type='doctor').count(),
        'active_programs': RehabilitationProgram.objects.filter(status='active').count(),
        'today_appointments': Consultation.objects.filter(start_time__date=timezone.now().date()).count(),
    }
    
    # Останні дії в системі
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    context = {
        'stats': stats,
        'recent_users': recent_users,
    }
    
    return render(request, 'core/admin_dashboard.html', context)


def therapist_dashboard(request):
    """Дашборд терапевта"""
    # Перевіряємо авторизацію та роль вручну
    if not request.user.is_authenticated:
        return redirect('core:login')
    
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'doctor':
        messages.error(request, 'Доступ заборонено. Тільки для терапевтів.')
        logout(request)
        return redirect('core:home')
    
    try:
        therapist = request.user.staff_profile
    except:
        messages.error(request, 'Профіль терапевта не знайдено.')
        logout(request)
        return redirect('core:home')
    
    # Отримуємо поточну дату з врахуванням часової зони
    now = timezone.now()
    today = now.date()
    
    # Найближчі прийоми (включаючи сьогоднішні та майбутні)
    today_appointments = Consultation.objects.filter(
        doctor=therapist,
        start_time__date__gte=today
    ).select_related('patient__user').order_by('start_time')
    
    # Пацієнти терапевта з підрахунком активних програм
    my_patients = PatientProfile.objects.filter(
        assigned_doctors=therapist
    ).annotate(
        active_programs_count=Count('rehab_programs', filter=Q(rehab_programs__status='active'))
    ).order_by('user__last_name')

    # Активні програми реабілітації
    active_programs = RehabilitationProgram.objects.filter(
        doctor=therapist,
        status='active'
    ).order_by('-created_at')[:5]

    # Статистика
    stats = {
        'total_patients': my_patients.count(),
        'active_programs': RehabilitationProgram.objects.filter(
            doctor=therapist, status='active'
        ).count(),
        'today_appointments': Consultation.objects.filter(
            doctor=therapist,
            start_time__date=today
        ).count(),
        'completed_appointments_this_week': Consultation.objects.filter(
            doctor=therapist,
            start_time__week=today.isocalendar()[1],
            status='completed'
        ).count(),
    }
    
    context = {
        'therapist': therapist,
        'today_appointments': today_appointments[:5], # Обмеження для відображення
        'active_programs': active_programs,
        'my_patients': my_patients[:10],  # Обмеження для відображення
        'stats': stats,
    }
    
    return render(request, 'core/therapist_dashboard.html', context)


def patient_dashboard(request):
    """Дашборд пацієнта"""
    # Перевіряємо авторизацію та роль вручну без декоратора
    if not request.user.is_authenticated:
        return redirect('core:login')
    
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'patient':
        messages.error(request, 'Доступ заборонено. Тільки для пацієнтів.')
        logout(request)
        return redirect('core:home')
    
    try:
        patient = request.user.patient_profile
    except:
        messages.error(request, 'Профіль пацієнта не знайдено.')
        logout(request)
        return redirect('core:home')
    
    today = timezone.now().date()
    
    # Найближчі прийоми
    upcoming_appointments = Consultation.objects.filter(
        patient=patient,
        start_time__gte=timezone.now(),
        status='scheduled'
    ).order_by('start_time')[:5]
    
    # Активні програми
    active_programs = RehabilitationProgram.objects.filter(
        patient=patient,
        status='active'
    ).order_by('-created_at')[:5]
    
    # Останні записи прогресу
    recent_progress = ExerciseSession.objects.filter(
        patient=patient
    ).order_by('-date')[:5]
    
    # Статистика
    stats = {
        'active_programs': active_programs.count() if active_programs else RehabilitationProgram.objects.filter(
            patient=patient, status='active'
        ).count(),
        'upcoming_appointments': upcoming_appointments.count() if upcoming_appointments else Consultation.objects.filter(
            patient=patient, start_time__gte=timezone.now(), status='scheduled'
        ).count(),
        'total_progress_logs': ExerciseSession.objects.filter(patient=patient).count(),
        'assigned_doctors': patient.assigned_doctors.count(),
    }
    
    context = {
        'patient': patient,
        'stats': stats,
        'upcoming_appointments': upcoming_appointments,
        'active_programs': active_programs,
        'recent_progress': recent_progress,
    }
    
    return render(request, 'core/patient_dashboard.html', context)


@therapist_or_admin_required
def patient_list(request):
    """Список пацієнтів для терапевтів та адміністраторів"""
    # Базовий QuerySet залежно від ролі
    if request.user.user_type == 'admin':
        patients_qs = PatientProfile.objects.all()
    else:  # doctor
        try:
            therapist = request.user.staff_profile
            patients_qs = PatientProfile.objects.filter(assigned_doctors=therapist)
        except:
            patients_qs = PatientProfile.objects.none()
    
    # Пошук
    search_query = request.GET.get('search', '')
    if search_query:
        patients_qs = patients_qs.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Пагінація
    paginator = Paginator(patients_qs.select_related('user'), 20)
    page_number = request.GET.get('page')
    patients = paginator.get_page(page_number)
    
    context = {
        'patients': patients,
        'search_query': search_query,
    }
    
    return render(request, 'core/patient_list.html', context)


@therapist_or_admin_required  
def all_patients_list(request):
    """Список всіх пацієнтів в системі (для лікарів та адміністраторів)"""
    # Показуємо всіх пацієнтів незалежно від ролі
    patients_qs = PatientProfile.objects.all()
    
    # Пошук
    search_query = request.GET.get('search', '')
    if search_query:
        patients_qs = patients_qs.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Пагінація
    paginator = Paginator(patients_qs.select_related('user'), 20)
    page_number = request.GET.get('page')
    patients = paginator.get_page(page_number)
    
    context = {
        'patients': patients,
        'search_query': search_query,
        'show_all': True,  # Флаг для шаблону що це список всіх пацієнтів
    }
    
    return render(request, 'core/patient_list.html', context)


@therapist_or_admin_required
def patient_detail(request, patient_id):
    """Детальна інформація про пацієнта"""
    patient = get_object_or_404(PatientProfile, id=patient_id)
    
    # Перевірка доступу
    if not check_patient_access(request.user, patient_id):
        messages.error(request, 'У вас немає доступу до даних цього пацієнта.')
        return redirect('core:patient_list')
    
    # Програми реабілітації
    programs = RehabilitationProgram.objects.filter(
        patient=patient
    ).order_by('-created_at')[:10]
    
    # Записи на прийом
    appointments = Consultation.objects.filter(
        patient=patient
    ).order_by('-start_time')[:10]
    
    # Прогрес
    progress_logs = ExerciseSession.objects.filter(
        patient=patient
    ).order_by('-date')[:10]
    
    # Медична історія
    try:
        medical_history = patient.medical_history
    except MedicalHistory.DoesNotExist:
        medical_history = None
    
    # Історія реабілітації
    rehabilitation_history = RehabilitationHistory.objects.filter(
        patient=patient
    ).order_by('-created_at')
    
    context = {
        'patient': patient,
        'programs': programs,
        'appointments': appointments,
        'progress_logs': progress_logs,
        'medical_history': medical_history,
        'rehabilitation_history': rehabilitation_history,
    }
    
    return render(request, 'core/patient_detail.html', context)


@admin_required
def get_available_doctors(request):
    """AJAX: Отримати список доступних лікарів"""
    patient_id = request.GET.get('patient_id')
    if not patient_id:
        return JsonResponse({'error': 'Patient ID required'}, status=400)
    
    try:
        patient = PatientProfile.objects.get(id=patient_id)
        # Отримуємо всіх лікарів, крім вже призначених
        assigned_doctor_ids = patient.assigned_doctors.values_list('id', flat=True)
        available_doctors = StaffProfile.objects.filter(
            user__user_type='doctor'
        ).exclude(id__in=assigned_doctor_ids).select_related('user')
        
        doctors_data = []
        for doctor in available_doctors:
            doctors_data.append({
                'id': doctor.id,
                'name': doctor.user.get_full_name(),
                'specialization': doctor.specialization or 'Не вказано',
                'email': doctor.user.email
            })
        
        return JsonResponse({'doctors': doctors_data})
    except PatientProfile.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)


@admin_required
@require_POST
def assign_doctor_to_patient(request):
    """AJAX: Призначити лікаря пацієнту"""
    print(f"Assign doctor request received: {request.method}")
    print(f"Request body: {request.body}")
    try:
        import json
        data = json.loads(request.body)
        patient_id = data.get('patient_id')
        doctor_id = data.get('doctor_id')
        
        if not patient_id or not doctor_id:
            return JsonResponse({'error': 'Patient ID and Doctor ID required'}, status=400)
        
        patient = PatientProfile.objects.get(id=patient_id)
        doctor = StaffProfile.objects.get(id=doctor_id, user__user_type='doctor')
        
        # Перевіряємо, чи лікар вже призначений
        if patient.assigned_doctors.filter(id=doctor_id).exists():
            return JsonResponse({'error': 'Doctor already assigned'}, status=400)
        
        # Призначаємо лікаря
        patient.assigned_doctors.add(doctor)
        
        return JsonResponse({
            'success': True,
            'doctor': {
                'id': doctor.id,
                'name': doctor.user.get_full_name(),
                'specialization': doctor.specialization or 'Не вказано'
            }
        })
        
    except (PatientProfile.DoesNotExist, StaffProfile.DoesNotExist):
        return JsonResponse({'error': 'Patient or Doctor not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@admin_required
@require_POST
def remove_doctor_from_patient(request):
    """AJAX: Видалити лікаря з пацієнта"""
    try:
        import json
        data = json.loads(request.body)
        patient_id = data.get('patient_id')
        doctor_id = data.get('doctor_id')
        
        if not patient_id or not doctor_id:
            return JsonResponse({'error': 'Patient ID and Doctor ID required'}, status=400)
        
        patient = PatientProfile.objects.get(id=patient_id)
        doctor = StaffProfile.objects.get(id=doctor_id)
        
        # Видаляємо лікаря
        patient.assigned_doctors.remove(doctor)
        
        return JsonResponse({'success': True})
        
    except (PatientProfile.DoesNotExist, StaffProfile.DoesNotExist):
        return JsonResponse({'error': 'Patient or Doctor not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)