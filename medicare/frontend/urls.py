from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    
    # This is the new loader URL
    path('dashboard/', views.dashboard, name='dashboard'), 
    
    # Role-specific dashboards
    path('dashboard/doctor/', views.doctor_dashboard_view, name='doctor_dashboard'),
    path('dashboard/patient/', views.patient_dashboard_view, name='patient_dashboard'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),

    path('profile/', views.profile, name='profile'),
    
    # Сторінки для лікарів
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('schedules/', views.schedule, name='schedule'),
    
    # Сторінки для пацієнтів
    path('my-programs/', views.my_programs, name='my_programs'),
    path('my-programs/<int:program_id>/', views.program_detail, name='program_detail'),
    path('my-doctors/', views.my_doctors, name='my_doctors'),
]