"""
URL конфігурація для основного функціоналу
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    # Головні сторінки
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('force-logout/', views.force_logout, name='force_logout'),
    
    # Відновлення пароля
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='core/password_reset_form.html',
        email_template_name='core/password_reset_email.html',
        success_url='/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='core/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='core/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='core/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Дашборди
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('therapist-dashboard/', views.therapist_dashboard, name='therapist_dashboard'),
    path('patient-dashboard/', views.patient_dashboard, name='patient_dashboard'),
    
    # Список пацієнтів (для терапевтів та адмінів)
    path('patients/', views.patient_list, name='patient_list'),
    path('all-patients/', views.all_patients_list, name='all_patients_list'),
    path('patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    
    # AJAX endpoints для призначення лікарів
    path('ajax/available-doctors/', views.get_available_doctors, name='get_available_doctors'),
    path('ajax/assign-doctor/', views.assign_doctor_to_patient, name='assign_doctor_to_patient'),
    path('ajax/remove-doctor/', views.remove_doctor_from_patient, name='remove_doctor_from_patient'),
]