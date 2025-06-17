from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'reports', views.ReportViewSet)

app_name = 'reports'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Report management
    path('', views.ReportDashboardView.as_view(), name='dashboard'),
    path('create/', views.CreateReportView.as_view(), name='create_report'),
    path('<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('<int:pk>/export/', views.ExportReportView.as_view(), name='export_report'),
    
    # Predefined reports
    path('patient-progress/', views.PatientProgressReportView.as_view(), name='patient_progress'),
    path('program-completion/', views.ProgramCompletionReportView.as_view(), name='program_completion'),
    path('doctor-activity/', views.DoctorActivityReportView.as_view(), name='doctor_activity'),
    path('survey-results/', views.SurveyResultsReportView.as_view(), name='survey_results'),
    path('system-usage/', views.SystemUsageReportView.as_view(), name='system_usage'),
    
    # Analytics endpoints
    path('analytics/patient/<int:patient_id>/', views.PatientAnalyticsView.as_view(), name='patient_analytics'),
    path('analytics/program/<int:program_id>/', views.ProgramAnalyticsView.as_view(), name='program_analytics'),
    path('analytics/overview/', views.SystemOverviewView.as_view(), name='system_overview'),
    
    # Export endpoints
    path('export/pdf/<int:report_id>/', views.ExportPDFView.as_view(), name='export_pdf'),
    path('export/csv/<int:report_id>/', views.ExportCSVView.as_view(), name='export_csv'),
    path('export/excel/<int:report_id>/', views.ExportExcelView.as_view(), name='export_excel'),
]