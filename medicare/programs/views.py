from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import models
import json
import logging
from rest_framework import viewsets, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import RehabilitationProgram, Appointment
from .serializers import RehabilitationProgramSerializer, RehabilitationProgramLightSerializer, AppointmentSerializer
from .forms import RehabilitationProgramForm

logger = logging.getLogger(__name__)
from staff.models import StaffProfile
from patients.models import PatientProfile


class IsOwnerOrAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object (or admins) to edit it.
    Patients get read-only access.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            if request.user.user_type == 'patient':
                return obj.patient.user == request.user
            return True

        if request.user.user_type == 'admin':
            return True
        
        if request.user.user_type == 'doctor':
            return obj.doctor.user == request.user
        
        return False


class RehabilitationProgramViewSet(viewsets.ModelViewSet):
    """
    API endpoint for rehabilitation programs.
    - Admins can manage all programs.
    - Doctors can manage programs for their assigned patients.
    - Patients can only view their own assigned programs.
    """
    queryset = RehabilitationProgram.objects.all().select_related('patient__user', 'doctor__user').prefetch_related('program_days__exercises__exercise')
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'list':
            return RehabilitationProgramLightSerializer
        return RehabilitationProgramSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.user_type == 'doctor':
            try:
                staff_profile = user.staff_profile
                return queryset.filter(doctor=staff_profile)
            except StaffProfile.DoesNotExist:
                return RehabilitationProgram.objects.none()
        
        if user.user_type == 'patient':
            try:
                patient_profile = user.patient_profile
                return queryset.filter(patient=patient_profile)
            except PatientProfile.DoesNotExist:
                return RehabilitationProgram.objects.none()
        
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.user_type != 'doctor' and user.user_type != 'admin':
            raise PermissionDenied("Only doctors or admins can create programs.")

        doctor_id = self.request.data.get('doctor_id')
        patient_id = self.request.data.get('patient_id')
        
        try:
            doctor = StaffProfile.objects.get(pk=doctor_id)
            patient = PatientProfile.objects.get(pk=patient_id)
        except (StaffProfile.DoesNotExist, PatientProfile.DoesNotExist):
            raise serializers.ValidationError("Invalid doctor or patient ID.")

        # A doctor can only create programs for their own patients
        if user.user_type == 'doctor' and patient not in user.staff_profile.patients.all():
            raise PermissionDenied("You can only create programs for your assigned patients.")

        serializer.save(doctor=doctor, patient=patient)


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for appointments.
    """
    queryset = Appointment.objects.all().select_related('patient__user', 'doctor__user')
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if user.user_type == 'doctor':
            try:
                staff_profile = user.staff_profile
                return queryset.filter(doctor=staff_profile)
            except StaffProfile.DoesNotExist:
                return Appointment.objects.none()
        
        if user.user_type == 'patient':
            try:
                patient_profile = user.patient_profile
                return queryset.filter(patient=patient_profile)
            except PatientProfile.DoesNotExist:
                return Appointment.objects.none()
        
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.user_type != 'doctor' and user.user_type != 'admin':
            raise PermissionDenied("Only doctors or admins can create appointments.")

        if user.user_type == 'doctor':
            serializer.save(doctor=user.staff_profile)


# Web Views (Class-Based Views for program management)
class ProgramListView(LoginRequiredMixin, ListView):
    model = RehabilitationProgram
    template_name = 'programs/program_list.html'
    context_object_name = 'programs'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        queryset = RehabilitationProgram.objects.all().select_related('patient__user', 'doctor__user')

        if user.user_type == 'doctor':
            try:
                staff_profile = user.staff_profile
                return queryset.filter(doctor=staff_profile)
            except StaffProfile.DoesNotExist:
                return RehabilitationProgram.objects.none()
        
        if user.user_type == 'patient':
            try:
                patient_profile = user.patient_profile
                return queryset.filter(patient=patient_profile)
            except PatientProfile.DoesNotExist:
                return RehabilitationProgram.objects.none()
        
        return queryset


class ProgramDetailView(LoginRequiredMixin, DetailView):
    model = RehabilitationProgram
    template_name = 'programs/program_detail.html'
    context_object_name = 'program'


class ProgramCreateView(LoginRequiredMixin, CreateView):
    model = RehabilitationProgram
    form_class = RehabilitationProgramForm
    template_name = 'programs/program_form.html'
    success_url = reverse_lazy('programs:program_list')

    def dispatch(self, request, *args, **kwargs):
        # Перевіряємо, чи користувач автентифікований
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        # Перевіряємо, чи користувач має право створювати програми
        if not hasattr(request.user, 'user_type') or request.user.user_type not in ['doctor', 'admin']:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Тільки лікарі та адміністратори можуть створювати програми.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if hasattr(self.request.user, 'user_type') and self.request.user.user_type == 'doctor':
            if hasattr(self.request.user, 'staff_profile'):
                form.instance.doctor = self.request.user.staff_profile
        return super().form_valid(form)


class ProgramUpdateView(LoginRequiredMixin, UpdateView):
    model = RehabilitationProgram
    template_name = 'programs/program_form.html'
    fields = ['title', 'description', 'start_date', 'end_date', 'status', 'goals', 'expected_outcomes', 'sessions_per_week', 'session_duration']
    success_url = reverse_lazy('programs:program_list')


class ProgramDeleteView(LoginRequiredMixin, DeleteView):
    model = RehabilitationProgram
    template_name = 'programs/program_confirm_delete.html'
    success_url = reverse_lazy('programs:program_list')


class ProgramAssignView(LoginRequiredMixin, CreateView):
    model = Appointment
    template_name = 'programs/program_assign.html'
    fields = ['patient', 'appointment_type', 'date', 'start_time', 'end_time', 'description']
    success_url = reverse_lazy('programs:assignment_list')

    def form_valid(self, form):
        if self.request.user.user_type == 'doctor':
            form.instance.doctor = self.request.user.staff_profile
        return super().form_valid(form)


class AssignmentListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = 'programs/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 10


class AssignmentDetailView(LoginRequiredMixin, DetailView):
    model = Appointment
    template_name = 'programs/assignment_detail.html'
    context_object_name = 'assignment'


class ProgramTemplateListView(LoginRequiredMixin, ListView):
    model = RehabilitationProgram
    template_name = 'programs/template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        # Використовуємо статус або інший критерій замість is_template
        return RehabilitationProgram.objects.filter(status='draft', patient__isnull=True)


class ProgramTemplateCreateView(LoginRequiredMixin, CreateView):
    model = RehabilitationProgram
    template_name = 'programs/template_form.html'
    fields = ['title', 'description', 'goals', 'sessions_per_week', 'session_duration']
    success_url = reverse_lazy('programs:template_list')

    def form_valid(self, form):
        # Встановлюємо статус як шаблон (використовуємо існуючий статус)
        form.instance.status = 'draft'
        # Для шаблону не встановлюємо пацієнта та дати
        form.instance.patient = None
        form.instance.start_date = None
        if self.request.user.user_type == 'doctor':
            form.instance.doctor = self.request.user.staff_profile
        return super().form_valid(form)


class ProgramLibraryView(LoginRequiredMixin, TemplateView):
    template_name = 'programs/program_library.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = RehabilitationProgram.objects.filter(status='draft', patient__isnull=True)
        context['public_programs'] = RehabilitationProgram.objects.filter(status='active')
        return context


@login_required
@require_POST
def change_program_status(request, program_id):
    """
    AJAX view for changing program status
    """
    try:
        program = get_object_or_404(RehabilitationProgram, id=program_id)
        
        # Check permissions
        user_has_permission = (request.user.user_type == 'admin' or 
                              (request.user.user_type == 'doctor' and program.doctor.user == request.user))
        
        if not user_has_permission:
            return JsonResponse({
                'success': False, 
                'message': 'У вас немає прав для зміни статусу цієї програми'
            }, status=403)
        
        # Parse request data
        data = json.loads(request.body)
        new_status = data.get('status')
        
        # Validate status
        valid_statuses = ['draft', 'active', 'completed', 'paused', 'cancelled']
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'message': 'Недійсний статус програми'
            }, status=400)
        
        # Validate status transitions
        current_status = program.status
        valid_transitions = {
            'draft': ['active', 'cancelled'],
            'active': ['paused', 'completed', 'cancelled'],
            'paused': ['active', 'cancelled'],
            'completed': [],
            'cancelled': []
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            return JsonResponse({
                'success': False,
                'message': f'Неможливо змінити статус з "{current_status}" на "{new_status}"'
            }, status=400)
        
        # Update status
        old_status = program.status
        program.status = new_status
        program.save()
        
        # Create a log entry if needed
        from .models import ProgressLog
        ProgressLog.objects.create(
            patient=program.patient,
            doctor=program.doctor,
            progress_type='general',
            notes=f'Статус програми "{program.title}" змінено з "{old_status}" на "{new_status}"',
            related_program=program
        )
        
        status_display = dict(RehabilitationProgram.STATUS_CHOICES).get(new_status, new_status)
        
        return JsonResponse({
            'success': True,
            'message': f'Статус програми успішно змінено на "{status_display}"',
            'new_status': new_status,
            'new_status_display': status_display
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Помилка обробки даних'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Помилка сервера: {str(e)}'
        }, status=500)


@login_required
@require_POST
def add_exercise_to_program(request):
    """
    Add exercise to rehabilitation program
    """
    try:
        data = json.loads(request.body)
        exercise_id = data.get('exercise_id')
        program_id = data.get('program_id')
        
        # Get program and check permissions
        program = get_object_or_404(RehabilitationProgram, id=program_id)
        
        if not (request.user.user_type == 'admin' or 
                (request.user.user_type == 'doctor' and program.doctor.user == request.user)):
            return JsonResponse({
                'success': False,
                'message': 'У вас немає прав для редагування цієї програми'
            }, status=403)
        
        # Get exercise
        from exercises.models import Exercise
        exercise = get_object_or_404(Exercise, id=exercise_id)
        
        # Get or create program day (we'll add to day 1 for simplicity)
        from .models import ProgramDay, ProgramExercise
        program_day, created = ProgramDay.objects.get_or_create(
            program=program,
            day_number=1,
            defaults={'notes': 'Автоматично створений день для вправ'}
        )
        
        # Check if exercise already exists in this program
        existing_exercise = ProgramExercise.objects.filter(
            program_day__program=program,
            exercise=exercise
        ).first()
        
        if existing_exercise:
            return JsonResponse({
                'success': False,
                'message': 'Ця вправа вже додана до програми'
            })
        
        # Get next order number
        max_order = ProgramExercise.objects.filter(program_day=program_day).aggregate(
            max_order=models.Max('order')
        )['max_order'] or 0
        
        # Create program exercise
        program_exercise = ProgramExercise.objects.create(
            program_day=program_day,
            exercise=exercise,
            sets=data.get('sets', 3),
            repetitions=data.get('repetitions', 10),
            duration=data.get('duration'),
            rest_between_sets=data.get('rest_between_sets', 60),
            additional_instructions=data.get('additional_instructions', ''),
            days_of_week=data.get('days_of_week', []),
            order=max_order + 1
        )
        
        # Create progress log
        from .models import ProgressLog
        ProgressLog.objects.create(
            patient=program.patient,
            doctor=program.doctor,
            progress_type='general',
            notes=f'Додано вправу "{exercise.title}" до програми "{program.title}"',
            related_program=program,
            related_exercise=exercise
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Вправу "{exercise.title}" успішно додано до програми',
            'program_exercise_id': program_exercise.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Помилка обробки даних'
        }, status=400)
    except Exception as e:
        logger.error(f"Error adding exercise to program: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Помилка сервера: {str(e)}'
        }, status=500)


@login_required
@require_POST
def add_program_day(request, program_id):
    """Додати день до програми реабілітації"""
    try:
        program = get_object_or_404(RehabilitationProgram, id=program_id)
        
        # Перевірка доступу
        if request.user.user_type == 'doctor' and program.doctor.user != request.user:
            return JsonResponse({'success': False, 'error': 'Немає доступу'})
        elif request.user.user_type not in ['doctor', 'admin']:
            return JsonResponse({'success': False, 'error': 'Немає доступу'})
        
        day_number = int(request.POST.get('day_number'))
        description = request.POST.get('description', '')
        
        # Перевірка, чи день уже існує
        from .models import ProgramDay
        if ProgramDay.objects.filter(program=program, day_number=day_number).exists():
            return JsonResponse({'success': False, 'error': f'День {day_number} вже існує в програмі'})
        
        # Створення нового дня
        program_day = ProgramDay.objects.create(
            program=program,
            day_number=day_number,
            notes=description
        )
        
        return JsonResponse({
            'success': True,
            'message': f'День {day_number} успішно додано до програми',
            'day_id': program_day.id
        })
        
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Неправильний номер дня'})
    except Exception as e:
        logger.error(f"Error adding program day: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST  
def add_exercise_to_day(request):
    """Додати вправу до конкретного дня програми"""
    try:
        day_id = request.POST.get('day_id')
        exercise_id = request.POST.get('exercise_id')
        
        from .models import ProgramDay, ProgramExercise
        from exercises.models import Exercise
        
        program_day = get_object_or_404(ProgramDay, id=day_id)
        exercise = get_object_or_404(Exercise, id=exercise_id)
        
        # Перевірка доступу
        if request.user.user_type == 'doctor' and program_day.program.doctor.user != request.user:
            return JsonResponse({'success': False, 'error': 'Немає доступу'})
        elif request.user.user_type not in ['doctor', 'admin']:
            return JsonResponse({'success': False, 'error': 'Немає доступу'})
        
        # Перевірка, чи вправа вже додана до цього дня
        if ProgramExercise.objects.filter(program_day=program_day, exercise=exercise).exists():
            return JsonResponse({'success': False, 'error': 'Ця вправа вже додана до цього дня'})
        
        # Отримання параметрів
        sets = int(request.POST.get('sets', 3))
        repetitions = int(request.POST.get('repetitions', 10))
        duration = request.POST.get('duration')
        if duration:
            duration = int(duration)
        rest_between_sets = int(request.POST.get('rest_between_sets', 60))
        additional_instructions = request.POST.get('additional_instructions', '')
        
        # Отримання наступного порядкового номера
        max_order = ProgramExercise.objects.filter(program_day=program_day).aggregate(
            max_order=models.Max('order')
        )['max_order'] or 0
        
        # Створення вправи програми
        program_exercise = ProgramExercise.objects.create(
            program_day=program_day,
            exercise=exercise,
            sets=sets,
            repetitions=repetitions,
            duration=duration,
            rest_between_sets=rest_between_sets,
            additional_instructions=additional_instructions,
            order=max_order + 1
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Вправу "{exercise.title}" успішно додано до дня {program_day.day_number}',
            'program_exercise_id': program_exercise.id
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': 'Неправильні числові параметри'})
    except Exception as e:
        logger.error(f"Error adding exercise to day: {e}")
        return JsonResponse({'success': False, 'error': str(e)})
