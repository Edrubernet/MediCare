import json
import os
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import GoogleCalendarCredentials, GoogleCalendarEvent
from .serializers import GoogleCalendarEventSerializer
from consultation.models import Consultation


class GoogleCalendarEventViewSet(viewsets.ModelViewSet):
    serializer_class = GoogleCalendarEventSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return GoogleCalendarEvent.objects.filter(user=self.request.user)


class GoogleCalendarAuthView(LoginRequiredMixin, View):
    """Початок OAuth flow для Google Calendar"""
    
    def get(self, request):
        # Налаштування OAuth flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                    "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [os.getenv('GOOGLE_REDIRECT_URI')]
                }
            },
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        
        flow.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        # Зберігаємо state в сесії для безпеки
        request.session['oauth_state'] = state
        
        return HttpResponseRedirect(authorization_url)


class GoogleCalendarCallbackView(LoginRequiredMixin, View):
    """Обробка callback від Google OAuth"""
    
    def get(self, request):
        # Перевіряємо state для безпеки
        if request.GET.get('state') != request.session.get('oauth_state'):
            messages.error(request, _('OAuth state mismatch. Please try again.'))
            return redirect('google_calendar:dashboard')
        
        # Отримуємо код авторизації
        code = request.GET.get('code')
        if not code:
            messages.error(request, _('Authorization code not received.'))
            return redirect('google_calendar:dashboard')
        
        try:
            # Обмінюємо код на токени
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [os.getenv('GOOGLE_REDIRECT_URI')]
                    }
                },
                scopes=['https://www.googleapis.com/auth/calendar'],
                state=request.session.get('oauth_state')
            )
            
            flow.redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
            flow.fetch_token(code=code)
            
            credentials = flow.credentials
            
            # Зберігаємо credentials в базі даних
            cred_obj, created = GoogleCalendarCredentials.objects.update_or_create(
                user=request.user,
                defaults={
                    'access_token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_expiry': credentials.expiry,
                }
            )
            
            messages.success(request, _('Google Calendar successfully connected!'))
            
        except Exception as e:
            messages.error(request, _('Failed to connect Google Calendar: %(error)s') % {'error': str(e)})
        
        return redirect('google_calendar:dashboard')


class DisconnectGoogleCalendarView(LoginRequiredMixin, View):
    """Від'єднання від Google Calendar"""
    
    def post(self, request):
        try:
            credentials = GoogleCalendarCredentials.objects.get(user=request.user)
            credentials.delete()
            messages.success(request, _('Google Calendar disconnected successfully.'))
        except GoogleCalendarCredentials.DoesNotExist:
            messages.info(request, _('Google Calendar was not connected.'))
        
        return redirect('google_calendar:dashboard')


class CalendarDashboardView(LoginRequiredMixin, TemplateView):
    """Головна сторінка календаря"""
    template_name = 'google_calendar/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Перевіряємо чи підключений Google Calendar
        try:
            credentials = GoogleCalendarCredentials.objects.get(user=self.request.user)
            context['google_connected'] = True
            context['credentials'] = credentials
        except GoogleCalendarCredentials.DoesNotExist:
            context['google_connected'] = False
        
        # Отримуємо останні події
        context['recent_events'] = GoogleCalendarEvent.objects.filter(
            user=self.request.user
        ).order_by('-start_time')[:10]
        
        return context


class SyncCalendarView(LoginRequiredMixin, View):
    """Синхронізація з Google Calendar"""
    
    def post(self, request):
        try:
            credentials_obj = GoogleCalendarCredentials.objects.get(user=request.user)
            
            # Створюємо credentials об'єкт
            credentials = Credentials(
                token=credentials_obj.access_token,
                refresh_token=credentials_obj.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
            )
            
            # Перевіряємо чи потрібно оновити токен
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                # Оновлюємо токен в базі даних
                credentials_obj.access_token = credentials.token
                credentials_obj.token_expiry = credentials.expiry
                credentials_obj.save()
            
            # Підключаємося до Google Calendar API
            service = build('calendar', 'v3', credentials=credentials)
            
            # Отримуємо події за останній місяць
            now = datetime.utcnow()
            time_min = (now - timedelta(days=30)).isoformat() + 'Z'
            time_max = (now + timedelta(days=30)).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Синхронізуємо події
            synced_count = 0
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                
                # Конвертуємо в datetime
                if 'T' in start:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                else:
                    start_dt = datetime.fromisoformat(start + 'T00:00:00+00:00')
                    end_dt = datetime.fromisoformat(end + 'T23:59:59+00:00')
                
                # Створюємо або оновлюємо подію
                google_event, created = GoogleCalendarEvent.objects.update_or_create(
                    user=request.user,
                    google_event_id=event['id'],
                    defaults={
                        'event_summary': event.get('summary', ''),
                        'event_description': event.get('description', ''),
                        'start_time': start_dt,
                        'end_time': end_dt,
                        'last_synced': now
                    }
                )
                
                if created or google_event.last_synced < now - timedelta(minutes=5):
                    synced_count += 1
            
            messages.success(request, _('Calendar synchronized successfully. %(count)d events updated.') % {'count': synced_count})
            
        except GoogleCalendarCredentials.DoesNotExist:
            messages.error(request, _('Google Calendar not connected. Please connect first.'))
        except Exception as e:
            messages.error(request, _('Sync failed: %(error)s') % {'error': str(e)})
        
        return redirect('google_calendar:dashboard')


class EventListView(LoginRequiredMixin, ListView):
    """Список подій календаря"""
    model = GoogleCalendarEvent
    template_name = 'google_calendar/event_list.html'
    context_object_name = 'events'
    paginate_by = 20
    
    def get_queryset(self):
        return GoogleCalendarEvent.objects.filter(user=self.request.user).order_by('-start_time')


class CreateEventFromConsultationView(LoginRequiredMixin, View):
    """Створення події в Google Calendar з консультації"""
    
    def post(self, request, consultation_id):
        consultation = get_object_or_404(Consultation, id=consultation_id)
        
        # Перевіряємо права доступу
        if not (consultation.doctor == request.user or consultation.patient.user == request.user):
            messages.error(request, _('You do not have permission to access this consultation.'))
            return redirect('consultation:detail', pk=consultation_id)
        
        try:
            credentials_obj = GoogleCalendarCredentials.objects.get(user=request.user)
            
            # Створюємо credentials об'єкт
            credentials = Credentials(
                token=credentials_obj.access_token,
                refresh_token=credentials_obj.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
            )
            
            # Оновлюємо токен при потребі
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                credentials_obj.access_token = credentials.token
                credentials_obj.token_expiry = credentials.expiry
                credentials_obj.save()
            
            # Підключаємося до Google Calendar API
            service = build('calendar', 'v3', credentials=credentials)
            
            # Створюємо подію
            event = {
                'summary': f'Консультація з {consultation.patient.user.get_full_name()}',
                'description': f'Консультація в системі Medicare\nПацієнт: {consultation.patient.user.get_full_name()}\nСтатус: {consultation.get_status_display()}',
                'start': {
                    'dateTime': consultation.scheduled_date.isoformat(),
                    'timeZone': 'Europe/Kiev',
                },
                'end': {
                    'dateTime': (consultation.scheduled_date + timedelta(hours=1)).isoformat(),
                    'timeZone': 'Europe/Kiev',
                },
            }
            
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            
            # Зберігаємо подію в базі даних
            google_event = GoogleCalendarEvent.objects.create(
                user=request.user,
                google_event_id=created_event['id'],
                consultation=consultation,
                event_summary=event['summary'],
                event_description=event['description'],
                start_time=consultation.scheduled_date,
                end_time=consultation.scheduled_date + timedelta(hours=1),
                last_synced=datetime.now()
            )
            
            messages.success(request, _('Event created in Google Calendar successfully.'))
            
        except GoogleCalendarCredentials.DoesNotExist:
            messages.error(request, _('Google Calendar not connected. Please connect first.'))
        except Exception as e:
            messages.error(request, _('Failed to create event: %(error)s') % {'error': str(e)})
        
        return redirect('consultation:detail', pk=consultation_id)


class SyncStatusView(LoginRequiredMixin, View):
    """API endpoint для статусу синхронізації"""
    
    def get(self, request):
        try:
            credentials = GoogleCalendarCredentials.objects.get(user=request.user)
            last_sync = GoogleCalendarEvent.objects.filter(user=request.user).order_by('-last_synced').first()
            
            return JsonResponse({
                'connected': True,
                'last_sync': last_sync.last_synced.isoformat() if last_sync else None,
                'events_count': GoogleCalendarEvent.objects.filter(user=request.user).count()
            })
        except GoogleCalendarCredentials.DoesNotExist:
            return JsonResponse({'connected': False})


class CalendarSettingsView(LoginRequiredMixin, TemplateView):
    """Налаштування календаря"""
    template_name = 'google_calendar/settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            context['credentials'] = GoogleCalendarCredentials.objects.get(user=self.request.user)
            context['google_connected'] = True
        except GoogleCalendarCredentials.DoesNotExist:
            context['google_connected'] = False
        
        return context


# Заглушки для інших views, які будуть реалізовані пізніше
class EventDetailView(LoginRequiredMixin, DetailView):
    model = GoogleCalendarEvent
    template_name = 'google_calendar/event_detail.html'
    context_object_name = 'event'


class CreateEventView(LoginRequiredMixin, CreateView):
    model = GoogleCalendarEvent
    template_name = 'google_calendar/create_event.html'
    fields = ['title', 'description', 'start_time', 'end_time', 'location']
    success_url = reverse_lazy('google_calendar:event_list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        # Спроба створити подію в Google Calendar
        try:
            self._create_google_event(self.object)
            messages.success(self.request, 'Подію створено та синхронізовано з Google Calendar')
        except Exception as e:
            messages.warning(self.request, f'Подію створено локально, але не вдалося синхронізувати з Google Calendar: {str(e)}')
        
        return response
    
    def _create_google_event(self, event):
        """Створити подію в Google Calendar"""
        try:
            credentials = GoogleCalendarCredentials.objects.get(user=self.request.user)
            creds = Credentials(
                token=credentials.access_token,
                refresh_token=credentials.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
            )
            
            service = build('calendar', 'v3', credentials=creds)
            
            google_event = {
                'summary': event.title,
                'description': event.description,
                'start': {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': 'Europe/Kyiv',
                },
                'end': {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': 'Europe/Kyiv',
                },
            }
            
            if event.location:
                google_event['location'] = event.location
            
            created_event = service.events().insert(calendarId='primary', body=google_event).execute()
            
            # Зберігаємо Google ID події
            event.google_event_id = created_event['id']
            event.save()
            
        except GoogleCalendarCredentials.DoesNotExist:
            raise Exception('Google Calendar не підключено')
        except Exception as e:
            raise Exception(f'Помилка Google Calendar API: {str(e)}')


class UpdateEventView(LoginRequiredMixin, UpdateView):
    model = GoogleCalendarEvent
    template_name = 'google_calendar/update_event.html'
    fields = ['title', 'description', 'start_time', 'end_time', 'location']
    success_url = reverse_lazy('google_calendar:event_list')
    
    def get_queryset(self):
        return GoogleCalendarEvent.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Спроба оновити подію в Google Calendar
        try:
            self._update_google_event(self.object)
            messages.success(self.request, 'Подію оновлено та синхронізовано з Google Calendar')
        except Exception as e:
            messages.warning(self.request, f'Подію оновлено локально, але не вдалося синхронізувати з Google Calendar: {str(e)}')
        
        return response
    
    def _update_google_event(self, event):
        """Оновити подію в Google Calendar"""
        if not event.google_event_id:
            raise Exception('Подія не синхронізована з Google Calendar')
        
        try:
            credentials = GoogleCalendarCredentials.objects.get(user=self.request.user)
            creds = Credentials(
                token=credentials.access_token,
                refresh_token=credentials.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
            )
            
            service = build('calendar', 'v3', credentials=creds)
            
            google_event = {
                'summary': event.title,
                'description': event.description,
                'start': {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': 'Europe/Kyiv',
                },
                'end': {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': 'Europe/Kyiv',
                },
            }
            
            if event.location:
                google_event['location'] = event.location
            
            service.events().update(
                calendarId='primary', 
                eventId=event.google_event_id, 
                body=google_event
            ).execute()
            
        except GoogleCalendarCredentials.DoesNotExist:
            raise Exception('Google Calendar не підключено')
        except Exception as e:
            raise Exception(f'Помилка Google Calendar API: {str(e)}')


class DeleteEventView(LoginRequiredMixin, View):
    def post(self, request, event_id):
        try:
            event = GoogleCalendarEvent.objects.get(id=event_id, user=request.user)
            
            # Спроба видалити подію з Google Calendar
            if event.google_event_id:
                try:
                    self._delete_google_event(event)
                except Exception as e:
                    messages.warning(request, f'Подію видалено локально, але не вдалося видалити з Google Calendar: {str(e)}')
            
            # Видаляємо локальну подію
            event.delete()
            messages.success(request, 'Подію видалено успішно')
            
        except GoogleCalendarEvent.DoesNotExist:
            messages.error(request, 'Подію не знайдено')
        except Exception as e:
            messages.error(request, f'Помилка при видаленні події: {str(e)}')
        
        return redirect('google_calendar:event_list')
    
    def _delete_google_event(self, event):
        """Видалити подію з Google Calendar"""
        try:
            credentials = GoogleCalendarCredentials.objects.get(user=event.user)
            creds = Credentials(
                token=credentials.access_token,
                refresh_token=credentials.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
            )
            
            service = build('calendar', 'v3', credentials=creds)
            service.events().delete(calendarId='primary', eventId=event.google_event_id).execute()
            
        except GoogleCalendarCredentials.DoesNotExist:
            raise Exception('Google Calendar не підключено')
        except Exception as e:
            raise Exception(f'Помилка Google Calendar API: {str(e)}')


class SyncConsultationView(LoginRequiredMixin, View):
    def post(self, request, consultation_id):
        try:
            from consultation.models import Consultation
            consultation = Consultation.objects.get(id=consultation_id)
            
            # Перевіряємо права доступу
            if request.user != consultation.patient.user and request.user != consultation.doctor.user:
                messages.error(request, 'Немає прав для синхронізації цієї консультації')
                return redirect('consultation:detail', pk=consultation_id)
            
            # Створюємо або оновлюємо подію в календарі
            event, created = GoogleCalendarEvent.objects.get_or_create(
                user=request.user,
                consultation=consultation,
                defaults={
                    'title': f'Консультація: {consultation.title}',
                    'description': f'Консультація з {consultation.doctor.user.get_full_name()}\n{consultation.description}',
                    'start_time': consultation.scheduled_datetime,
                    'end_time': consultation.scheduled_datetime + timedelta(hours=1),
                    'location': consultation.location or 'Онлайн'
                }
            )
            
            # Синхронізуємо з Google Calendar
            try:
                if created:
                    self._create_google_event(event)
                else:
                    self._update_google_event(event)
                
                messages.success(request, 'Консультацію синхронізовано з Google Calendar')
            except Exception as e:
                messages.warning(request, f'Подію створено локально, але не вдалося синхронізувати з Google Calendar: {str(e)}')
            
        except Consultation.DoesNotExist:
            messages.error(request, 'Консультацію не знайдено')
        except Exception as e:
            messages.error(request, f'Помилка при синхронізації: {str(e)}')
        
        return redirect('consultation:detail', pk=consultation_id)
    
    def _create_google_event(self, event):
        """Створити подію консультації в Google Calendar"""
        try:
            credentials = GoogleCalendarCredentials.objects.get(user=event.user)
            creds = Credentials(
                token=credentials.access_token,
                refresh_token=credentials.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
            )
            
            service = build('calendar', 'v3', credentials=creds)
            
            google_event = {
                'summary': event.title,
                'description': event.description,
                'start': {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': 'Europe/Kyiv',
                },
                'end': {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': 'Europe/Kyiv',
                },
                'location': event.location
            }
            
            created_event = service.events().insert(calendarId='primary', body=google_event).execute()
            
            # Зберігаємо Google ID події
            event.google_event_id = created_event['id']
            event.save()
            
        except Exception as e:
            raise Exception(f'Помилка створення події в Google Calendar: {str(e)}')
    
    def _update_google_event(self, event):
        """Оновити подію консультації в Google Calendar"""
        if not event.google_event_id:
            return self._create_google_event(event)
        
        try:
            credentials = GoogleCalendarCredentials.objects.get(user=event.user)
            creds = Credentials(
                token=credentials.access_token,
                refresh_token=credentials.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET')
            )
            
            service = build('calendar', 'v3', credentials=creds)
            
            google_event = {
                'summary': event.title,
                'description': event.description,
                'start': {
                    'dateTime': event.start_time.isoformat(),
                    'timeZone': 'Europe/Kyiv',
                },
                'end': {
                    'dateTime': event.end_time.isoformat(),
                    'timeZone': 'Europe/Kyiv',
                },
                'location': event.location
            }
            
            service.events().update(
                calendarId='primary',
                eventId=event.google_event_id,
                body=google_event
            ).execute()
            
        except Exception as e:
            raise Exception(f'Помилка оновлення події в Google Calendar: {str(e)}')


class GoogleCalendarWebhookView(View):
    def post(self, request):
        """Обробка Google Calendar webhook notifications"""
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Отримуємо заголовки з Google
            channel_id = request.META.get('HTTP_X_GOOG_CHANNEL_ID')
            channel_token = request.META.get('HTTP_X_GOOG_CHANNEL_TOKEN')
            resource_id = request.META.get('HTTP_X_GOOG_RESOURCE_ID')
            resource_state = request.META.get('HTTP_X_GOOG_RESOURCE_STATE')
            
            logger.info(f'Google Calendar webhook received: channel_id={channel_id}, state={resource_state}')
            
            # Перевіряємо, чи це дійсний webhook від Google
            if not channel_id or not resource_id:
                logger.warning('Invalid webhook: missing required headers')
                return JsonResponse({'error': 'Invalid webhook'}, status=400)
            
            # Обробляємо різні типи подій
            if resource_state == 'sync':
                # Початкова синхронізація - нічого не робимо
                logger.info('Sync event received, no action needed')
                
            elif resource_state == 'exists':
                # Подія була змінена - оновлюємо локальні дані
                self._handle_calendar_change(channel_id, resource_id)
                
            else:
                logger.info(f'Unhandled resource state: {resource_state}')
            
            return JsonResponse({'status': 'ok'})
            
        except Exception as e:
            logger.error(f'Error processing Google Calendar webhook: {str(e)}')
            return JsonResponse({'error': 'Processing failed'}, status=500)
    
    def _handle_calendar_change(self, channel_id, resource_id):
        """Обробляє зміни в календарі Google"""
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Тут можна реалізувати логіку синхронізації:
            # 1. Знайти користувача за channel_id
            # 2. Отримати оновлені події з Google Calendar API
            # 3. Оновити локальні записи
            
            # Поки що просто логуємо
            logger.info(f'Calendar change detected for channel {channel_id}, resource {resource_id}')
            
            # Можна додати повідомлення користувачам про зміни в календарі
            from django.contrib.auth import get_user_model
            from notification.models import Notification
            
            # Знаходимо користувачів, які мають активні webhook підписки
            # та надсилаємо їм повідомлення про зміни в календарі
            
        except Exception as e:
            logger.error(f'Error handling calendar change: {str(e)}')


class VerifyWebhookView(View):
    def get(self, request):
        """Верифікація Google Calendar webhook endpoint"""
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Google надсилає GET запит для верифікації endpoint
            challenge = request.GET.get('hub.challenge')
            verify_token = request.GET.get('hub.verify_token')
            
            # Перевіряємо токен (можна встановити через змінні середовища)
            expected_token = os.getenv('GOOGLE_WEBHOOK_VERIFY_TOKEN', 'medicare-webhook-token')
            
            if verify_token and verify_token == expected_token:
                logger.info('Webhook verification successful')
                # Повертаємо challenge для підтвердження
                return HttpResponse(challenge, content_type='text/plain')
            else:
                logger.warning(f'Webhook verification failed: invalid token {verify_token}')
                return HttpResponse('Verification failed', status=403)
                
        except Exception as e:
            logger.error(f'Error during webhook verification: {str(e)}')
            return HttpResponse('Verification error', status=500)
    
    def post(self, request):
        """Альтернативний метод для верифікації через POST"""
        return self.get(request)


class NotificationSettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'google_calendar/notification_settings.html'
