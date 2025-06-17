from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'programs', views.RehabilitationProgramViewSet)
router.register(r'appointments', views.AppointmentViewSet)

app_name = 'programs'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Program management views
    path('', views.ProgramListView.as_view(), name='program_list'),
    path('my-programs/', views.ProgramListView.as_view(), name='patient_programs'),  # Alias for patients
    path('create/', views.ProgramCreateView.as_view(), name='program_create'),
    path('<int:pk>/', views.ProgramDetailView.as_view(), name='program_detail'),
    path('<int:pk>/edit/', views.ProgramUpdateView.as_view(), name='program_edit'),
    path('<int:pk>/delete/', views.ProgramDeleteView.as_view(), name='program_delete'),
    path('<int:program_id>/status/', views.change_program_status, name='change_program_status'),
    path('add-exercise/', views.add_exercise_to_day, name='add_exercise_to_day'),
    path('<int:program_id>/add-day/', views.add_program_day, name='add_program_day'),
    
    # Program assignments
    path('assign/', views.ProgramAssignView.as_view(), name='program_assign'),
    path('assignments/', views.AssignmentListView.as_view(), name='assignment_list'),
    path('assignments/<int:pk>/', views.AssignmentDetailView.as_view(), name='assignment_detail'),
    
    # Templates and library
    path('templates/', views.ProgramTemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.ProgramTemplateCreateView.as_view(), name='template_create'),
    path('library/', views.ProgramLibraryView.as_view(), name='program_library'),
] 