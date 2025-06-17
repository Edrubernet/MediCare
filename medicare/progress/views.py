from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied
from .models import ExerciseSession, ExerciseCompletion, PatientNote, RehabilitationGoal, GoalProgress
from .serializers import (
    ExerciseSessionSerializer, ExerciseCompletionSerializer, 
    PatientNoteSerializer, RehabilitationGoalSerializer, RehabilitationGoalLightSerializer,
    GoalProgressSerializer
)
from staff.models import StaffProfile
from patients.models import PatientProfile
from programs.models import RehabilitationProgram


class IsOwnerOrAssignedDoctorOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.user_type == 'admin':
            return True
        
        patient_profile = None
        if hasattr(obj, 'patient'):
            patient_profile = obj.patient
        elif hasattr(obj, 'session') and hasattr(obj.session, 'patient'):
            patient_profile = obj.session.patient
        
        if not patient_profile:
            return False

        if user.user_type == 'patient':
            return patient_profile.user == user
        
        if user.user_type == 'doctor':
            return patient_profile in user.staff_profile.patients.all()
            
        return False


class ExerciseSessionViewSet(viewsets.ModelViewSet):
    queryset = ExerciseSession.objects.all()
    serializer_class = ExerciseSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssignedDoctorOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            return super().get_queryset()
        if user.user_type == 'patient':
            return self.queryset.filter(patient__user=user)
        if user.user_type == 'doctor':
            return self.queryset.filter(patient__in=user.staff_profile.patients.all())
        return ExerciseSession.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.user_type != 'patient':
            raise PermissionDenied("Only patients can log exercise sessions.")
        
        program_id = self.request.data.get('program_id')
        program = RehabilitationProgram.objects.get(pk=program_id)
        
        if program.patient.user != user:
            raise PermissionDenied("You can only log sessions for your own programs.")

        serializer.save(patient=user.patient_profile, program=program)



class PatientNoteViewSet(viewsets.ModelViewSet):
    queryset = PatientNote.objects.all()
    serializer_class = PatientNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssignedDoctorOrAdmin]

    def get_queryset(self):
        user = self.request.user
        patient_id = self.request.query_params.get('patient_id')

        if user.user_type == 'admin':
            qs = super().get_queryset()
        elif user.user_type == 'doctor':
            qs = self.queryset.filter(patient__in=user.staff_profile.patients.all())
        elif user.user_type == 'patient':
            qs = self.queryset.filter(patient__user=user)
        else:
            qs = PatientNote.objects.none()

        if patient_id:
            return qs.filter(patient_id=patient_id)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        if user.user_type != 'doctor':
            raise PermissionDenied("Only doctors can create patient notes.")
        
        patient_id = self.request.data.get('patient_id')
        patient = PatientProfile.objects.get(pk=patient_id)

        if patient not in user.staff_profile.patients.all():
            raise PermissionDenied("You can only create notes for your assigned patients.")
            
        serializer.save(doctor=user.staff_profile, patient=patient)


class ExerciseProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for exercise completion tracking (progress).
    """
    queryset = ExerciseCompletion.objects.all()
    serializer_class = ExerciseCompletionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssignedDoctorOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            return super().get_queryset()
        if user.user_type == 'patient':
            return self.queryset.filter(session__patient__user=user)
        if user.user_type == 'doctor':
            return self.queryset.filter(session__patient__in=user.staff_profile.patients.all())
        return ExerciseCompletion.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.user_type != 'patient':
            raise PermissionDenied("Only patients can log exercise completions.")
        
        session_id = self.request.data.get('session_id')
        session = ExerciseSession.objects.get(pk=session_id)
        
        if session.patient.user != user:
            raise PermissionDenied("You can only log completions for your own sessions.")

        serializer.save(session=session)


# Web Views (Class-Based Views for progress management)
class ProgressDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'progress/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.user_type == 'patient':
            context['recent_sessions'] = ExerciseSession.objects.filter(
                patient__user=user
            ).order_by('-date')[:5]
        elif user.user_type == 'doctor':
            context['patient_sessions'] = ExerciseSession.objects.filter(
                patient__in=user.staff_profile.patients.all()
            ).order_by('-date')[:10]
        
        return context


class PatientProgressView(LoginRequiredMixin, DetailView):
    template_name = 'progress/patient_progress.html'
    context_object_name = 'patient'
    
    def get_object(self):
        from patients.models import PatientProfile
        patient_id = self.kwargs.get('patient_id')
        return PatientProfile.objects.get(pk=patient_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.get_object()
        context['sessions'] = ExerciseSession.objects.filter(patient=patient).order_by('-date')
        context['notes'] = PatientNote.objects.filter(patient=patient).order_by('-created_at')
        return context


class ProgramProgressView(LoginRequiredMixin, DetailView):
    template_name = 'progress/program_progress.html'
    context_object_name = 'program'
    
    def get_object(self):
        program_id = self.kwargs.get('program_id')
        return RehabilitationProgram.objects.get(pk=program_id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        program = self.get_object()
        context['sessions'] = ExerciseSession.objects.filter(program=program).order_by('-date')
        return context


class TrackExerciseView(LoginRequiredMixin, CreateView):
    model = ExerciseCompletion
    template_name = 'progress/track_exercise.html'
    fields = ['sets_completed', 'repetitions_completed', 'pain_level', 'difficulty_level', 'notes']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from exercises.models import Exercise
        exercise_id = self.kwargs.get('exercise_id')
        context['exercise'] = Exercise.objects.get(pk=exercise_id)
        return context


class StartExerciseSessionView(LoginRequiredMixin, CreateView):
    model = ExerciseSession
    template_name = 'progress/start_session.html'
    fields = ['program', 'date', 'notes']
    success_url = reverse_lazy('progress:progress_dashboard')
    
    def form_valid(self, form):
        if self.request.user.user_type == 'patient':
            form.instance.patient = self.request.user.patient_profile
        return super().form_valid(form)


class CompleteExerciseSessionView(LoginRequiredMixin, UpdateView):
    model = ExerciseSession
    template_name = 'progress/complete_session.html'
    fields = ['completed', 'notes']
    success_url = reverse_lazy('progress:progress_dashboard')
    
    def get_object(self):
        session_id = self.kwargs.get('session_id')
        return ExerciseSession.objects.get(pk=session_id)



class CreatePatientNoteView(LoginRequiredMixin, CreateView):
    model = PatientNote
    template_name = 'progress/create_note.html'
    fields = ['patient', 'note']
    success_url = reverse_lazy('progress:progress_dashboard')
    
    def form_valid(self, form):
        if self.request.user.user_type == 'doctor':
            form.instance.doctor = self.request.user.staff_profile
        return super().form_valid(form)


class ProgressAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'progress/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.user_type == 'patient':
            sessions = ExerciseSession.objects.filter(patient__user=user)
            context['total_sessions'] = sessions.count()
            context['completed_sessions'] = sessions.filter(completed=True).count()
        elif user.user_type == 'doctor':
            patients = user.staff_profile.patients.all()
            context['total_patients'] = patients.count()
            context['active_programs'] = RehabilitationProgram.objects.filter(
                patient__in=patients, status='active'
            ).count()
        
        return context


class ExportProgressView(LoginRequiredMixin, TemplateView):
    template_name = 'progress/export.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.user_type == 'doctor':
            context['patients'] = user.staff_profile.patients.all()
        elif user.user_type == 'admin':
            context['patients'] = PatientProfile.objects.all()
            
        return context
    
    def post(self, request, *args, **kwargs):
        from django.http import HttpResponse
        import json
        
        # Get form data
        format_type = request.POST.get('format')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        include_sessions = request.POST.get('include_sessions')
        include_exercises = request.POST.get('include_exercises')
        include_photos = request.POST.get('include_photos')
        include_notes = request.POST.get('include_notes')
        patient_id = request.POST.get('patient_id')
        
        # For now, return a simple response
        # In a real implementation, you would generate the actual export file
        response_data = {
            'success': True,
            'message': f'Експорт у форматі {format_type} буде готовий незабаром',
            'format': format_type,
            'period': f'{start_date} - {end_date}' if start_date and end_date else 'Всі дані'
        }
        
        return HttpResponse(
            json.dumps(response_data, ensure_ascii=False),
            content_type='application/json'
        )


class RehabilitationGoalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing rehabilitation goals.
    """
    queryset = RehabilitationGoal.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssignedDoctorOrAdmin]

    def get_serializer_class(self):
        if self.action == 'list':
            return RehabilitationGoalLightSerializer
        return RehabilitationGoalSerializer

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'admin':
            return super().get_queryset()
        if user.user_type == 'patient':
            return self.queryset.filter(patient__user=user)
        if user.user_type == 'doctor':
            return self.queryset.filter(patient__in=user.staff_profile.patients.all())
        return RehabilitationGoal.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.user_type not in ['doctor', 'admin']:
            raise PermissionDenied("Only doctors and admins can create goals.")
        
        patient_id = self.request.data.get('patient_id')
        patient = PatientProfile.objects.get(pk=patient_id)

        if user.user_type == 'doctor' and patient not in user.staff_profile.patients.all():
            raise PermissionDenied("You can only create goals for your assigned patients.")
            
        serializer.save(doctor=user.staff_profile, patient=patient)

    def perform_update(self, serializer):
        user = self.request.user
        goal = self.get_object()
        
        if user.user_type == 'patient':
            # Patients can only update current_value
            allowed_fields = ['current_value']
            for field in serializer.validated_data.keys():
                if field not in allowed_fields:
                    raise PermissionDenied(f"Patients cannot update the '{field}' field.")
        
        # Update progress and check if goal is achieved
        if 'current_value' in serializer.validated_data:
            new_value = serializer.validated_data['current_value']
            goal.update_progress(new_value)
        
        serializer.save()


class GoalProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tracking progress on rehabilitation goals.
    """
    queryset = GoalProgress.objects.all()
    serializer_class = GoalProgressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssignedDoctorOrAdmin]

    def get_queryset(self):
        user = self.request.user
        goal_id = self.request.query_params.get('goal_id')
        
        if user.user_type == 'admin':
            qs = super().get_queryset()
        elif user.user_type == 'patient':
            qs = self.queryset.filter(goal__patient__user=user)
        elif user.user_type == 'doctor':
            qs = self.queryset.filter(goal__patient__in=user.staff_profile.patients.all())
        else:
            qs = GoalProgress.objects.none()

        if goal_id:
            return qs.filter(goal_id=goal_id)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        goal_id = self.request.data.get('goal_id')
        goal = RehabilitationGoal.objects.get(pk=goal_id)
        
        # Check permissions
        if user.user_type == 'patient' and goal.patient.user != user:
            raise PermissionDenied("You can only add progress to your own goals.")
        elif user.user_type == 'doctor' and goal.patient not in user.staff_profile.patients.all():
            raise PermissionDenied("You can only add progress to goals of your assigned patients.")
        
        # Save the progress entry
        recorded_by = user.staff_profile if user.user_type == 'doctor' else None
        progress_entry = serializer.save(goal=goal, recorded_by=recorded_by)
        
        # Update the goal's current value to the latest progress
        goal.update_progress(progress_entry.value)
