from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet)

app_name = 'notification'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Notification management views
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('unread/', views.UnreadNotificationView.as_view(), name='unread_notifications'),
    path('mark-all-read/', views.MarkAllReadView.as_view(), name='mark_all_read'),
    path('<int:pk>/mark-read/', views.MarkReadView.as_view(), name='mark_read'),
    
    # Settings
    path('settings/', views.NotificationSettingsView.as_view(), name='notification_settings'),
    path('preferences/', views.NotificationPreferencesView.as_view(), name='notification_preferences'),
] 