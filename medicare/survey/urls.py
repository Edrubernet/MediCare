from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'surveys', views.SurveyViewSet)
router.register(r'assignments', views.SurveyAssignmentViewSet)
router.register(r'responses', views.SurveyResponseViewSet)

app_name = 'survey'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Survey management for staff
    path('', views.SurveyListView.as_view(), name='survey_list'),
    path('create/', views.SurveyCreateView.as_view(), name='survey_create'),
    path('<int:pk>/', views.SurveyDetailView.as_view(), name='survey_detail'),
    path('<int:pk>/edit/', views.SurveyUpdateView.as_view(), name='survey_edit'),
    path('<int:pk>/delete/', views.SurveyDeleteView.as_view(), name='survey_delete'),
    
    # Survey assignments
    path('assign/', views.SurveyAssignView.as_view(), name='survey_assign'),
    path('assignments/', views.SurveyAssignmentListView.as_view(), name='assignment_list'),
    
    # Patient survey taking
    path('take/<int:assignment_id>/', views.TakeSurveyView.as_view(), name='take_survey'),
    path('submit/<int:assignment_id>/', views.SubmitSurveyView.as_view(), name='submit_survey'),
    
    # Survey results
    path('results/<int:survey_id>/', views.SurveyResultsView.as_view(), name='survey_results'),
    path('results/<int:survey_id>/export/', views.ExportSurveyResultsView.as_view(), name='export_results'),
]