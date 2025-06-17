"""
Головна URL конфігурація для Medicare MPA системи
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # Основний функціонал
    path('', include('core.urls')),
    
    # Модулі системи (включають API endpoints)
    path('patients/', include('patients.urls')),
    path('staff/', include('staff.urls')),
    path('exercises/', include('exercises.urls')),
    path('programs/', include('programs.urls')),
    path('progress/', include('progress.urls')),
    path('communications/', include('communications.urls')),
    path('notifications/', include('notification.urls')),
    path('consultation/', include('consultation.urls')),
    
    # Фронтенд (якщо залишився)
    path('frontend/', include('frontend.urls')),
]

# Статичні та медіа файли
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)