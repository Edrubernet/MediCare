"""
URL конфігурація для модуля пацієнтів (MPA + API)
"""
from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    # Список та деталі пацієнтів
    path('', views.patient_list, name='patient_list'),
    path('<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('<int:patient_id>/edit/', views.patient_edit, name='patient_edit'),
    
    # Медична історія
    path('<int:patient_id>/medical-history/edit/', 
         views.medical_history_edit, name='medical_history_edit'),
    
    # Записи реабілітації
    path('<int:patient_id>/rehabilitation/add/', 
         views.add_rehabilitation_record, name='add_rehabilitation_record'),
    path('<int:patient_id>/rehabilitation/<int:record_id>/', 
         views.rehabilitation_record_detail, name='rehabilitation_record_detail'),
    
    # AJAX endpoints для адміністраторів
    path('<int:patient_id>/assign-doctor/', 
         views.assign_doctor, name='assign_doctor'),
    
    # AJAX endpoints для лікарів
    path('<int:patient_id>/assign/', 
         views.toggle_patient_assignment, name='toggle_patient_assignment'),
    
    # Профіль для пацієнтів
    path('my-profile/', views.my_profile, name='my_profile'),
    
    # API endpoints
    path('api/search/', views.PatientSearchAPIView.as_view(), name='api_patient_search'),
    path('api/profiles/', views.PatientProfilesAPIView.as_view(), name='api_patient_profiles'),
    path('api/profiles/<int:patient_id>/assign/', 
         views.assign_patient_to_doctor_api, name='api_assign_patient'),
]