from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'events', views.GoogleCalendarEventViewSet)

app_name = 'google_calendar'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # OAuth flow
    path('auth/', views.GoogleCalendarAuthView.as_view(), name='auth'),
    path('callback/', views.GoogleCalendarCallbackView.as_view(), name='callback'),
    path('disconnect/', views.DisconnectGoogleCalendarView.as_view(), name='disconnect'),
    
    # Calendar management
    path('', views.CalendarDashboardView.as_view(), name='dashboard'),
    path('sync/', views.SyncCalendarView.as_view(), name='sync_calendar'),
    path('sync/status/', views.SyncStatusView.as_view(), name='sync_status'),
    
    # Event management
    path('events/', views.EventListView.as_view(), name='event_list'),
    path('events/create/', views.CreateEventView.as_view(), name='create_event'),
    path('events/<str:event_id>/', views.EventDetailView.as_view(), name='event_detail'),
    path('events/<str:event_id>/edit/', views.UpdateEventView.as_view(), name='update_event'),
    path('events/<str:event_id>/delete/', views.DeleteEventView.as_view(), name='delete_event'),
    
    # Consultation integration
    path('consultation/<int:consultation_id>/create-event/', views.CreateEventFromConsultationView.as_view(), name='create_event_from_consultation'),
    path('consultation/<int:consultation_id>/sync/', views.SyncConsultationView.as_view(), name='sync_consultation'),
    
    # Webhook endpoints
    path('webhook/', views.GoogleCalendarWebhookView.as_view(), name='webhook'),
    path('webhook/verify/', views.VerifyWebhookView.as_view(), name='verify_webhook'),
    
    # Settings
    path('settings/', views.CalendarSettingsView.as_view(), name='settings'),
    path('settings/notifications/', views.NotificationSettingsView.as_view(), name='notification_settings'),
]