from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Count, Q
from django.db import models
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView

from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, StaffProfile, Certificate, WorkSchedule
from .serializers import (UserSerializer, StaffProfileSerializer, 
                          CertificateSerializer, WorkScheduleSerializer, AppointmentSerializer)
from .permissions import IsAdminOrSelf, IsAdminOrOwner
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from django.db import transaction
from .serializers import RegisterSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrSelf]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['user_type']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    @action(detail=False, methods=['get'], url_path='me')
    def get_current_user(self, request):
        """
        Get the profile of the currently authenticated user.
        """
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class StaffProfileViewSet(viewsets.ModelViewSet):
    queryset = StaffProfile.objects.all().prefetch_related('certificates', 'work_schedules', 'patients')
    serializer_class = StaffProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['specialization']
    search_fields = ['user__first_name', 'user__last_name', 'specialization']
    
    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        staff = self.get_object()
        schedules = staff.work_schedules.all()
        serializer = WorkScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def patients(self, request, pk=None):
        staff = self.get_object()
        patients = staff.patients.all()
        from patients.serializers import PatientProfileSerializer
        serializer = PatientProfileSerializer(patients, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='me/appointments/today')
    def my_today_appointments(self, request):
        """
        Get today's appointments for the current staff member.
        """
        from datetime import date
        from programs.models import Appointment
        today = date.today()
        
        if request.user.user_type != 'doctor':
            return Response({'error': 'Only doctors can access this endpoint'}, status=403)
        
        try:
            staff = request.user.staff_profile
            appointments = Appointment.objects.filter(
                doctor=staff,
                date=today
            ).order_by('start_time')
            
            serializer = AppointmentSerializer(appointments, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class CertificateViewSet(viewsets.ModelViewSet):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]


class WorkScheduleViewSet(viewsets.ModelViewSet):
    queryset = WorkSchedule.objects.all()
    serializer_class = WorkScheduleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['staff', 'day_of_week']


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# Web Views (Class-Based Views for staff management)
class StaffDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'staff/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'total_staff': User.objects.filter(user_type='staff').count(),
            'active_patients': User.objects.filter(user_type='patient', is_active=True).count(),
            'recent_registrations': User.objects.filter(user_type='staff').order_by('-date_joined')[:5],
        })
        return context


class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'staff/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        user_type = self.request.GET.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        return queryset


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'staff/user_detail.html'
    context_object_name = 'user_detail'


class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    template_name = 'staff/user_form.html'
    fields = ['email', 'first_name', 'last_name', 'user_type', 'is_active']
    success_url = reverse_lazy('staff:user_list')


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'staff/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'user_type', 'is_active']
    success_url = reverse_lazy('staff:user_list')


class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = 'staff/user_confirm_delete.html'
    success_url = reverse_lazy('staff:user_list')


class StaffProfileListView(LoginRequiredMixin, ListView):
    model = StaffProfile
    template_name = 'staff/staff_list.html'
    context_object_name = 'staff_profiles'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = StaffProfile.objects.select_related('user').prefetch_related('patients').order_by('user__last_name', 'user__first_name')
        
        # Filter by specialization
        specialization = self.request.GET.get('specialization')
        if specialization:
            queryset = queryset.filter(specialization=specialization)
        
        # Search by name or specialization
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(specialization__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add statistics
        all_staff = StaffProfile.objects.all()
        context.update({
            'doctor_count': all_staff.filter(specialization='doctor').count(),
            'therapist_count': all_staff.filter(specialization='therapist').count(),
        })
        
        return context


class StaffProfileDetailView(LoginRequiredMixin, DetailView):
    model = StaffProfile
    template_name = 'staff/staff_detail.html'
    context_object_name = 'staff_profile'


class StaffProfileCreateView(LoginRequiredMixin, CreateView):
    model = StaffProfile
    template_name = 'staff/staff_form.html'
    fields = ['user', 'specialization', 'bio']
    success_url = reverse_lazy('staff:staff_profile_list')


class StaffProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = StaffProfile
    template_name = 'staff/staff_form.html'
    fields = ['specialization', 'bio']
    success_url = reverse_lazy('staff:staff_profile_list')


class CertificateListView(LoginRequiredMixin, ListView):
    model = Certificate
    template_name = 'staff/certificate_list.html'
    context_object_name = 'certificates'


class CertificateCreateView(LoginRequiredMixin, CreateView):
    model = Certificate
    template_name = 'staff/certificate_form.html'
    fields = ['staff', 'name', 'issuer', 'issue_date', 'expiry_date', 'file']
    success_url = reverse_lazy('staff:certificate_list')


class WorkScheduleListView(LoginRequiredMixin, ListView):
    model = WorkSchedule
    template_name = 'staff/schedule_list.html'
    context_object_name = 'schedules'


class WorkScheduleCreateView(LoginRequiredMixin, CreateView):
    model = WorkSchedule
    template_name = 'staff/schedule_form.html'
    fields = ['staff', 'day_of_week', 'start_time', 'end_time']
    success_url = reverse_lazy('staff:work_schedule')


class WorkScheduleUpdateView(LoginRequiredMixin, UpdateView):
    model = WorkSchedule
    template_name = 'staff/schedule_form.html'
    fields = ['staff', 'day_of_week', 'start_time', 'end_time']
    success_url = reverse_lazy('staff:work_schedule')


class CertificateDetailView(LoginRequiredMixin, DetailView):
    model = Certificate
    template_name = 'staff/certificate_detail.html'
    context_object_name = 'certificate'


class MyProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'staff/my_profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        if hasattr(user, 'staffprofile'):
            context['staff_profile'] = user.staffprofile
        return context


class MyProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'staff/my_profile_form.html'
    fields = ['first_name', 'last_name', 'email']
    success_url = reverse_lazy('staff:my_profile')
    
    def get_object(self):
        return self.request.user


class AppointmentListView(LoginRequiredMixin, ListView):
    template_name = 'staff/appointment_list.html'
    context_object_name = 'appointments'
    paginate_by = 20
    
    def get_queryset(self):
        from programs.models import Appointment
        user = self.request.user
        
        if user.user_type == 'admin':
            queryset = Appointment.objects.all()
        elif user.user_type == 'doctor':
            queryset = Appointment.objects.filter(doctor__user=user)
        elif user.user_type == 'patient':
            queryset = Appointment.objects.filter(patient__user=user)
        else:
            queryset = Appointment.objects.none()
        
        # Apply filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        appointment_type = self.request.GET.get('appointment_type')
        if appointment_type:
            queryset = queryset.filter(appointment_type=appointment_type)
        
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset.select_related('doctor__user', 'patient__user').order_by('-date', '-start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        context['status_choices'] = [
            ('scheduled', 'Заплановано'),
            ('confirmed', 'Підтверджено'),
            ('in_progress', 'В процесі'),
            ('completed', 'Завершено'),
            ('cancelled', 'Скасовано'),
            ('no_show', 'Не з\'явився'),
        ]
        
        context['type_choices'] = [
            ('consultation', 'Консультація'),
            ('therapy_session', 'Терапевтичний сеанс'),
            ('assessment', 'Оцінка'),
            ('follow_up', 'Повторний огляд'),
        ]
        
        return context


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['doctor', 'patient', 'status', 'date']
    search_fields = ['description', 'notes']
    
    
    def get_queryset(self):
        from programs.models import Appointment
        user = self.request.user
        if user.user_type == 'admin':
            return Appointment.objects.all()
        elif user.user_type == 'doctor':
            return Appointment.objects.filter(doctor__user=user)
        elif user.user_type == 'patient':
            return Appointment.objects.filter(patient__user=user)
        return Appointment.objects.none()
    
    @action(detail=False, methods=['get'], url_path='today')
    def today_appointments(self, request):
        """
        Get today's appointments for the current user.
        """
        from datetime import date
        from programs.models import Appointment
        today = date.today()
        
        if request.user.user_type == 'doctor':
            appointments = Appointment.objects.filter(
                doctor__user=request.user,
                date=today
            ).order_by('start_time')
        elif request.user.user_type == 'patient':
            appointments = Appointment.objects.filter(
                patient__user=request.user,
                date=today
            ).order_by('start_time')
        else:
            appointments = Appointment.objects.none()
        
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)