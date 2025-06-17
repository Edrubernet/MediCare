from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'exercise-progress', views.ExerciseProgressViewSet)
router.register(r'exercise-sessions', views.ExerciseSessionViewSet)
router.register(r'patient-notes', views.PatientNoteViewSet)
router.register(r'goals', views.RehabilitationGoalViewSet)
router.register(r'goal-progress', views.GoalProgressViewSet)

app_name = 'progress'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Progress tracking views
    path('', views.ProgressDashboardView.as_view(), name='progress_dashboard'),
    path('patient/<int:patient_id>/', views.PatientProgressView.as_view(), name='patient_progress'),
    path('program/<int:program_id>/', views.ProgramProgressView.as_view(), name='program_progress'),
    
    # Exercise tracking
    path('exercise/<int:exercise_id>/track/', views.TrackExerciseView.as_view(), name='track_exercise'),
    path('session/start/', views.StartExerciseSessionView.as_view(), name='start_session'),
    path('session/<int:session_id>/complete/', views.CompleteExerciseSessionView.as_view(), name='complete_session'),
    
    # Notes
    path('notes/create/', views.CreatePatientNoteView.as_view(), name='create_note'),
    
    # Analytics and reports
    path('analytics/', views.ProgressAnalyticsView.as_view(), name='progress_analytics'),
    path('export/', views.ExportProgressView.as_view(), name='export_progress'),
] 