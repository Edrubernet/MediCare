from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from .models import Consultation, ConsultationNote, ConsultationRecording
from .serializers import (
    ConsultationSerializer, ConsultationLightSerializer,
    ConsultationNoteSerializer, ConsultationRecordingSerializer
)
from .forms import ConsultationForm, QuickConsultationForm, ConsultationSearchForm, PatientConsultationRequestForm
from staff.models import StaffProfile
from patients.models import PatientProfile
from core.permissions import therapist_or_admin_required


class IsParticipantOrAdmin(permissions.BasePermission):
    """
    Permission to only allow participants of a consultation (or admins) to view it.
    Editing is restricted further in the view.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.user_type == 'admin':
            return True
        return obj.patient.user == user or obj.doctor.user == user


class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = Consultation.objects.all().select_related(
        'patient__user', 'doctor__user'
    ).prefetch_related('consultation_note', 'recording')
    permission_classes = [permissions.IsAuthenticated, IsParticipantOrAdmin]

    def get_serializer_class(self):
        if self.action == 'list':
            return ConsultationLightSerializer
        return ConsultationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            return super().get_queryset()
        
        return self.queryset.filter(Q(patient__user=user) | Q(doctor__user=user))

    def perform_create(self, serializer):
        user = self.request.user
        if user.user_type != 'patient':
            raise PermissionDenied("Only patients can request a consultation.")
        
        doctor_id = self.request.data.get('doctor_id')
        doctor = StaffProfile.objects.get(pk=doctor_id)
        
        # Check if the doctor is assigned to the patient
        if doctor not in user.patient_profile.assigned_doctors.all():
            raise PermissionDenied("You can only book consultations with your assigned doctors.")
        
        serializer.save(patient=user.patient_profile, doctor=doctor)

    def perform_update(self, serializer):
        user = self.request.user
        if user.user_type == 'patient' and 'status' in serializer.validated_data:
            raise PermissionDenied("Patients cannot change the status of a consultation.")
        
        # Additional logic can be added here, e.g. only doctors can change status.
        
        # --- Notification Logic ---
        # If status is updated, send a notification
        if 'status' in serializer.validated_data:
            from notification.models import Notification
            
            instance = serializer.instance
            new_status = serializer.validated_data['status']
            
            # Notify patient when doctor confirms/changes status
            if user.user_type == 'doctor':
                Notification.objects.create(
                    recipient=instance.patient.user,
                    notification_type='appointment',
                    title=f"Consultation Status Updated: {new_status.title()}",
                    message=f"Your consultation with Dr. {instance.doctor.user.get_full_name()} on {instance.start_time.strftime('%Y-%m-%d %H:%M')} has been updated to '{new_status}'."
                )

        serializer.save()

    @action(detail=True, methods=['post'])
    def reschedule(self, request, pk=None):
        """Reschedule a consultation to a new datetime"""
        consultation = self.get_object()
        
        # Check permissions - only doctor or admin can reschedule
        if request.user.user_type not in ['doctor', 'admin']:
            return Response(
                {'error': 'Only doctors or admins can reschedule consultations'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get new datetime from request
        new_datetime = request.data.get('datetime')
        reason = request.data.get('reason', '')
        notify_patient = request.data.get('notify_patient', True)
        
        if not new_datetime:
            return Response(
                {'error': 'New datetime is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from datetime import datetime
            new_datetime = datetime.fromisoformat(new_datetime.replace('Z', '+00:00'))
            
            # Calculate new end time (assuming same duration)
            duration = consultation.end_time - consultation.start_time
            new_end_time = new_datetime + duration
            
            # Update consultation
            consultation.start_time = new_datetime
            consultation.end_time = new_end_time
            consultation.save()
            
            # Send notification if requested
            if notify_patient:
                from notification.models import Notification
                Notification.objects.create(
                    recipient=consultation.patient.user,
                    notification_type='appointment',
                    title='Consultation Rescheduled',
                    message=f'Your consultation with Dr. {consultation.doctor.user.get_full_name()} has been rescheduled to {new_datetime.strftime("%Y-%m-%d %H:%M")}. Reason: {reason}'
                )
            
            serializer = self.get_serializer(consultation)
            return Response(serializer.data)
            
        except (ValueError, TypeError) as e:
            return Response(
                {'error': 'Invalid datetime format'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a consultation"""
        consultation = self.get_object()
        
        # Check permissions - only doctor, admin, or patient can cancel
        if request.user.user_type not in ['doctor', 'admin', 'patient']:
            return Response(
                {'error': 'Insufficient permissions'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if consultation can be cancelled
        if consultation.status in ['completed', 'canceled']:
            return Response(
                {'error': 'Cannot cancel a consultation that is already completed or cancelled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', 'Cancelled by user')
        notify_patient = request.data.get('notify_patient', True)
        
        # Update status
        consultation.status = 'canceled'
        consultation.notes = f"{consultation.notes or ''}\n\nCancellation reason: {reason}".strip()
        consultation.save()
        
        # Send notification
        if notify_patient and request.user.user_type != 'patient':
            from notification.models import Notification
            Notification.objects.create(
                recipient=consultation.patient.user,
                notification_type='appointment',
                title='Consultation Cancelled',
                message=f'Your consultation with Dr. {consultation.doctor.user.get_full_name()} on {consultation.start_time.strftime("%Y-%m-%d %H:%M")} has been cancelled. Reason: {reason}'
            )
        elif request.user.user_type == 'patient':
            # Notify doctor if patient cancels
            from notification.models import Notification
            Notification.objects.create(
                recipient=consultation.doctor.user,
                notification_type='appointment',
                title='Consultation Cancelled by Patient',
                message=f'Patient {consultation.patient.user.get_full_name()} has cancelled their consultation on {consultation.start_time.strftime("%Y-%m-%d %H:%M")}. Reason: {reason}'
            )
        
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a consultation (set status to in_progress)"""
        consultation = self.get_object()
        
        # Check permissions - only doctor or admin can start
        if request.user.user_type not in ['doctor', 'admin']:
            return Response(
                {'error': 'Only doctors or admins can start consultations'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if consultation.status != 'scheduled':
            return Response(
                {'error': 'Can only start scheduled consultations'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultation.status = 'in_progress'
        consultation.save()
        
        # Send notification to patient
        from notification.models import Notification
        Notification.objects.create(
            recipient=consultation.patient.user,
            notification_type='appointment',
            title='Consultation Started',
            message=f'Your consultation with Dr. {consultation.doctor.user.get_full_name()} has started.'
        )
        
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)


class ConsultationNoteViewSet(viewsets.ModelViewSet):
    queryset = ConsultationNote.objects.all()
    serializer_class = ConsultationNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsParticipantOrAdmin]
    # Simplified logic: permissions are checked based on the related consultation
    # A more robust implementation would use `has_object_permission` on the note's consultation

class ConsultationRecordingViewSet(viewsets.ModelViewSet):
    queryset = ConsultationRecording.objects.all()
    serializer_class = ConsultationRecordingSerializer
    permission_classes = [permissions.IsAuthenticated, IsParticipantOrAdmin]


# MPA Views для консультацій

@therapist_or_admin_required
def consultation_list(request):
    """Список консультацій для лікарів"""
    form = ConsultationSearchForm(request.GET)
    consultations_qs = Consultation.objects.select_related(
        'patient__user', 'doctor__user'
    ).order_by('-start_time')
    
    # Фільтрація для лікарів
    if request.user.user_type == 'doctor':
        consultations_qs = consultations_qs.filter(doctor=request.user.staff_profile)
    
    # Застосування фільтрів з форми
    if form.is_valid():
        search = form.cleaned_data.get('search')
        if search:
            consultations_qs = consultations_qs.filter(
                Q(patient__user__first_name__icontains=search) |
                Q(patient__user__last_name__icontains=search)
            )
        
        status = form.cleaned_data.get('status')
        if status:
            consultations_qs = consultations_qs.filter(status=status)
        
        consultation_type = form.cleaned_data.get('consultation_type')
        if consultation_type:
            consultations_qs = consultations_qs.filter(consultation_type=consultation_type)
        
        date_from = form.cleaned_data.get('date_from')
        if date_from:
            consultations_qs = consultations_qs.filter(start_time__date__gte=date_from)
        
        date_to = form.cleaned_data.get('date_to')
        if date_to:
            consultations_qs = consultations_qs.filter(start_time__date__lte=date_to)
        
        sort = form.cleaned_data.get('sort')
        if sort:
            consultations_qs = consultations_qs.order_by(sort)
    
    # Пагінація
    paginator = Paginator(consultations_qs, 20)
    page_number = request.GET.get('page')
    consultations = paginator.get_page(page_number)
    
    context = {
        'consultations': consultations,
        'form': form,
    }
    return render(request, 'consultation/consultation_list.html', context)


@therapist_or_admin_required
def consultation_create(request):
    """Створення нової консультації"""
    if request.method == 'POST':
        form = ConsultationForm(request.POST, user=request.user)
        if form.is_valid():
            consultation = form.save(commit=False)
            # Автоматично встановлюємо лікаря, якщо користувач - лікар і поле не заповнене
            if request.user.user_type == 'doctor' and not consultation.doctor:
                consultation.doctor = request.user.staff_profile
            consultation.save()
            
            messages.success(request, 'Консультацію успішно заплановано!')
            return redirect('consultation:consultation_detail', pk=consultation.pk)
        else:
            # Додаємо повідомлення про помилки для дебага
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ConsultationForm(user=request.user)
    
    # Додаємо інформацію про доступних пацієнтів
    patients_count = PatientProfile.objects.filter(user__is_active=True).count()
    
    context = {
        'form': form,
        'title': 'Запланувати консультацію',
        'patients_count': patients_count,
        'debug_user': request.user,
    }
    return render(request, 'consultation/consultation_form.html', context)


@therapist_or_admin_required
def quick_consultation_create(request):
    """Швидке створення консультації (AJAX)"""
    if request.method == 'POST':
        form = QuickConsultationForm(request.POST, user=request.user)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.doctor = request.user.staff_profile
            consultation.save()
            
            return JsonResponse({
                'success': True,
                'consultation_id': consultation.id,
                'message': 'Консультацію успішно заплановано!'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    form = QuickConsultationForm(user=request.user)
    context = {'form': form}
    return render(request, 'consultation/quick_consultation_modal.html', context)


def consultation_detail(request, pk):
    """Деталі консультації"""
    consultation = get_object_or_404(
        Consultation.objects.select_related('patient__user', 'doctor__user'),
        pk=pk
    )
    
    # Перевірка доступу
    if request.user.user_type == 'patient':
        if consultation.patient.user != request.user:
            messages.error(request, 'У вас немає доступу до цієї консультації')
            return redirect('core:patient_dashboard')
    elif request.user.user_type == 'doctor':
        if consultation.doctor.user != request.user:
            messages.error(request, 'У вас немає доступу до цієї консультації')
            return redirect('consultation:consultation_list')
    
    context = {
        'consultation': consultation,
    }
    return render(request, 'consultation/consultation_detail.html', context)


@require_POST
@login_required
def update_consultation_status(request, pk):
    """Оновлення статусу консультації (AJAX)"""
    consultation = get_object_or_404(Consultation, pk=pk)
    
    # Перевірка доступу - лікар може змінювати свої консультації, пацієнт може скасовувати свої
    if request.user.user_type == 'doctor' and consultation.doctor.user != request.user:
        return JsonResponse({'success': False, 'error': 'Немає доступу'})
    elif request.user.user_type == 'patient' and consultation.patient.user != request.user:
        return JsonResponse({'success': False, 'error': 'Немає доступу'})
    elif request.user.user_type not in ['doctor', 'patient', 'admin']:
        return JsonResponse({'success': False, 'error': 'Немає доступу'})
    
    new_status = request.POST.get('status')
    
    # Додаткова перевірка для пацієнтів - можуть тільки скасовувати
    if request.user.user_type == 'patient' and new_status != 'canceled':
        return JsonResponse({'success': False, 'error': 'Пацієнти можуть тільки скасовувати консультації'})
    
    if new_status in dict(Consultation.STATUS_CHOICES):
        consultation.status = new_status
        consultation.save()
        
        # Створюємо notification 
        from notification.models import Notification
        if request.user.user_type == 'patient':
            # Пацієнт скасовує - сповіщаємо лікаря
            Notification.objects.create(
                recipient=consultation.doctor.user,
                notification_type='appointment',
                title=f'Консультація скасована пацієнтом',
                message=f'Пацієнт {consultation.patient.user.get_full_name()} скасував консультацію від {consultation.start_time.strftime("%d.%m.%Y %H:%M")}'
            )
        else:
            # Лікар змінює статус - сповіщаємо пацієнта
            Notification.objects.create(
                recipient=consultation.patient.user,
                notification_type='appointment',
                title=f'Статус консультації змінено',
                message=f'Статус вашої консультації з {consultation.doctor.user.get_full_name()} змінено на "{consultation.get_status_display()}"'
            )
        
        return JsonResponse({
            'success': True,
            'new_status': consultation.get_status_display()
        })
    
    return JsonResponse({'success': False, 'error': 'Невірний статус'})


@login_required
def patient_search_ajax(request):
    """AJAX пошук пацієнтів для лікарів"""
    if request.user.user_type != 'doctor':
        return JsonResponse({'error': 'Доступ заборонено'})
    
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Пошук серед пацієнтів лікаря
    patients = PatientProfile.objects.filter(
        assigned_doctors=request.user.staff_profile,
        user__is_active=True
    ).filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__email__icontains=query)
    ).select_related('user')[:10]
    
    results = []
    for patient in patients:
        results.append({
            'id': patient.id,
            'text': f"{patient.user.get_full_name()} ({patient.user.email})",
            'name': patient.user.get_full_name(),
            'email': patient.user.email
        })
    
    return JsonResponse({'results': results})


@login_required
def patient_consultation_request(request):
    """Запит на консультацію від пацієнта"""
    if request.user.user_type != 'patient':
        messages.error(request, 'Доступ заборонено')
        return redirect('core:patient_dashboard')
    
    if request.method == 'POST':
        form = PatientConsultationRequestForm(request.POST, patient=request.user.patient_profile)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.patient = request.user.patient_profile
            consultation.status = 'scheduled'
            consultation.save()
            
            # Створюємо повідомлення лікарю
            from notification.models import Notification
            Notification.objects.create(
                recipient=consultation.doctor.user,
                notification_type='appointment',
                title='Новий запит на консультацію',
                message=f'Пацієнт {consultation.patient.user.get_full_name()} запросив консультацію на {consultation.start_time.strftime("%d.%m.%Y %H:%M")}'
            )
            
            messages.success(request, 'Запит на консультацію надіслано!')
            return redirect('consultation:patient_consultations')
    else:
        form = PatientConsultationRequestForm(patient=request.user.patient_profile)
    
    context = {
        'form': form,
        'title': 'Записатися на прийом'
    }
    return render(request, 'consultation/patient_consultation_request.html', context)


@login_required 
def patient_consultations(request):
    """Список консультацій пацієнта"""
    if request.user.user_type != 'patient':
        messages.error(request, 'Доступ заборонено')
        return redirect('core:patient_dashboard')
    
    consultations = Consultation.objects.filter(
        patient=request.user.patient_profile
    ).select_related('doctor__user').order_by('-start_time')
    
    # Пагінація
    paginator = Paginator(consultations, 10)
    page_number = request.GET.get('page')
    consultations_page = paginator.get_page(page_number)
    
    context = {
        'consultations': consultations_page,
        'title': 'Мої прийоми'
    }
    return render(request, 'consultation/patient_consultations.html', context)


@login_required
@require_POST
def consultation_notes(request, pk):
    """Збереження нотаток консультації (AJAX)"""
    consultation = get_object_or_404(Consultation, pk=pk)
    
    # Перевірка доступу - тільки лікар може додавати нотатки
    if request.user.user_type != 'doctor' or consultation.doctor.user != request.user:
        return JsonResponse({'success': False, 'error': 'Немає доступу'})
    
    import json
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Контент не може бути порожнім'})
        
        # Отримуємо або створюємо нотатку
        note, created = ConsultationNote.objects.get_or_create(
            consultation=consultation,
            defaults={'content': content}
        )
        
        if not created:
            # Оновлюємо існуючу нотатку
            note.content = content
            note.save()
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неправильний формат даних'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
