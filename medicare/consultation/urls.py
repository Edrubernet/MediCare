from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'consultations', views.ConsultationViewSet, basename='consultation')
router.register(r'notes', views.ConsultationNoteViewSet, basename='consultationnote')
router.register(r'recordings', views.ConsultationRecordingViewSet, basename='consultationrecording')

app_name = 'consultation'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # MPA views
    path('', views.consultation_list, name='consultation_list'),
    path('create/', views.consultation_create, name='consultation_create'),
    path('quick-create/', views.quick_consultation_create, name='quick_consultation_create'),
    path('<int:pk>/', views.consultation_detail, name='consultation_detail'),
    path('<int:pk>/update-status/', views.update_consultation_status, name='update_consultation_status'),
    path('<int:pk>/notes/', views.consultation_notes, name='consultation_notes'),
    
    # AJAX endpoints
    path('ajax/patient-search/', views.patient_search_ajax, name='patient_search_ajax'),
    
    # Patient views
    path('patient/request/', views.patient_consultation_request, name='patient_consultation_request'),
    path('patient/my-consultations/', views.patient_consultations, name='patient_consultations'),
] 