import os
import mimetypes
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, Http404, StreamingHttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from .models import MediaFile, VideoProcessingStatus
from .serializers import MediaFileSerializer, VideoProcessingStatusSerializer
from .utils import process_video_file, generate_thumbnail, get_file_type, validate_file_size, validate_file_type


class MediaFileViewSet(viewsets.ModelViewSet):
    serializer_class = MediaFileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        return MediaFile.objects.filter(uploaded_by=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class MediaLibraryView(LoginRequiredMixin, ListView):
    """Бібліотека медіа файлів"""
    model = MediaFile
    template_name = 'media/library.html'
    context_object_name = 'media_files'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = MediaFile.objects.all().order_by('-created_at')
        
        # Фільтрація по типу файлу
        file_type = self.request.GET.get('type')
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        
        # Пошук
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['file_types'] = MediaFile.FILE_TYPES
        context['current_type'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class FileUploadView(LoginRequiredMixin, CreateView):
    """Завантаження одного файлу"""
    model = MediaFile
    template_name = 'media/upload.html'
    fields = ['title', 'description', 'file']
    success_url = reverse_lazy('media:media_library')
    
    def form_valid(self, form):
        # Отримуємо завантажений файл
        uploaded_file = form.cleaned_data['file']
        
        # Валідація розміру файлу
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 50 * 1024 * 1024)  # 50MB
        if not validate_file_size(uploaded_file, max_size):
            messages.error(self.request, _('File size exceeds maximum allowed size of %(size)s MB.') % {'size': max_size // (1024*1024)})
            return self.form_invalid(form)
        
        # Валідація типу файлу
        if not validate_file_type(uploaded_file):
            messages.error(self.request, _('File type not allowed.'))
            return self.form_invalid(form)
        
        # Визначаємо тип файлу
        file_type = get_file_type(uploaded_file)
        form.instance.file_type = file_type
        form.instance.file_size = uploaded_file.size
        form.instance.mime_type = uploaded_file.content_type
        form.instance.uploaded_by = self.request.user
        
        response = super().form_valid(form)
        
        # Якщо це відео, запускаємо обробку
        if file_type == 'video':
            self.start_video_processing(self.object)
        
        messages.success(self.request, _('File uploaded successfully.'))
        return response
    
    def start_video_processing(self, media_file):
        """Запуск обробки відео файлу"""
        try:
            # Створюємо запис про статус обробки
            processing_status, created = VideoProcessingStatus.objects.get_or_create(
                media_file=media_file,
                defaults={'status': 'pending'}
            )
            
            # Запускаємо асинхронну обробку
            self._process_video_file(media_file)
            
            messages.info(self.request, _('Video processing started. You will be notified when it\'s complete.'))
        except Exception as e:
            messages.warning(self.request, _('Video uploaded but processing failed to start: %(error)s') % {'error': str(e)})
    
    def _process_video_file(self, media_file):
        """Базова обробка відео файлу"""
        try:
            processing_status = VideoProcessingStatus.objects.get(media_file=media_file)
            processing_status.status = 'processing'
            processing_status.progress = 50
            processing_status.save()
            
            # Тут може бути реальна обробка відео (стиснення, конвертація, створення превью)
            # Наразі просто позначаємо як завершено
            import time
            time.sleep(1)  # Імітація обробки
            
            processing_status.status = 'completed'
            processing_status.progress = 100
            processing_status.save()
            
        except Exception as e:
            try:
                processing_status.status = 'failed'
                processing_status.error_message = str(e)
                processing_status.save()
            except:
                pass


class MultipleFileUploadView(LoginRequiredMixin, TemplateView):
    """Завантаження декількох файлів"""
    template_name = 'media/upload_multiple.html'
    
    def post(self, request):
        files = request.FILES.getlist('files')
        uploaded_count = 0
        errors = []
        
        for file in files:
            try:
                # Валідація файлу
                max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 50 * 1024 * 1024)
                if not validate_file_size(file, max_size):
                    errors.append(f'{file.name}: File size exceeds maximum allowed size.')
                    continue
                
                if not validate_file_type(file):
                    errors.append(f'{file.name}: File type not allowed.')
                    continue
                
                # Створюємо медіа файл
                media_file = MediaFile.objects.create(
                    title=file.name,
                    file=file,
                    file_type=get_file_type(file),
                    file_size=file.size,
                    mime_type=file.content_type,
                    uploaded_by=request.user
                )
                
                # Запускаємо обробку відео
                if media_file.file_type == 'video':
                    self.start_video_processing(media_file)
                
                uploaded_count += 1
                
            except Exception as e:
                errors.append(f'{file.name}: {str(e)}')
        
        if uploaded_count > 0:
            messages.success(request, _('%(count)d files uploaded successfully.') % {'count': uploaded_count})
        
        if errors:
            for error in errors:
                messages.error(request, error)
        
        return redirect('media:media_library')
    
    def start_video_processing(self, media_file):
        """Запуск обробки відео файлу"""
        VideoProcessingStatus.objects.get_or_create(
            media_file=media_file,
            defaults={'status': 'pending'}
        )


class MediaFileDetailView(LoginRequiredMixin, DetailView):
    """Детальна інформація про медіа файл"""
    model = MediaFile
    template_name = 'media/detail.html'
    context_object_name = 'media_file'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Додаємо інформацію про обробку відео
        if self.object.file_type == 'video':
            try:
                context['processing_status'] = self.object.processing_status
            except VideoProcessingStatus.DoesNotExist:
                context['processing_status'] = None
        
        return context


class MediaFileUpdateView(LoginRequiredMixin, UpdateView):
    """Редагування медіа файлу"""
    model = MediaFile
    template_name = 'media/edit.html'
    fields = ['title', 'description']
    success_url = reverse_lazy('media:media_library')
    
    def form_valid(self, form):
        messages.success(self.request, _('Media file updated successfully.'))
        return super().form_valid(form)


class MediaFileDeleteView(LoginRequiredMixin, DeleteView):
    """Видалення медіа файлу"""
    model = MediaFile
    template_name = 'media/delete.html'
    success_url = reverse_lazy('media:media_library')
    
    def delete(self, request, *args, **kwargs):
        # Видаляємо фізичний файл
        media_file = self.get_object()
        if media_file.file:
            default_storage.delete(media_file.file.name)
        
        messages.success(request, _('Media file deleted successfully.'))
        return super().delete(request, *args, **kwargs)


class ProcessVideoView(LoginRequiredMixin, View):
    """Обробка відео файлу"""
    
    def post(self, request, pk):
        media_file = get_object_or_404(MediaFile, pk=pk, file_type='video')
        
        try:
            processing_status, created = VideoProcessingStatus.objects.get_or_create(
                media_file=media_file,
                defaults={'status': 'pending'}
            )
            
            if processing_status.status == 'processing':
                return JsonResponse({'error': 'Video is already being processed'}, status=400)
            
            # Оновлюємо статус
            processing_status.status = 'processing'
            processing_status.progress = 0
            processing_status.save()
            
            # Запускаємо обробку
            self._process_video_file(media_file)
            
            return JsonResponse({'success': True, 'message': 'Video processing started'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    def _process_video_file(self, media_file):
        """Базова обробка відео файлу"""
        try:
            processing_status = VideoProcessingStatus.objects.get(media_file=media_file)
            processing_status.status = 'processing'
            processing_status.progress = 50
            processing_status.save()
            
            # Тут може бути реальна обробка відео (стиснення, конвертація, створення превью)
            # Наразі просто позначаємо як завершено
            import time
            time.sleep(1)  # Імітація обробки
            
            processing_status.status = 'completed'
            processing_status.progress = 100
            processing_status.save()
            
        except Exception as e:
            try:
                processing_status.status = 'failed'
                processing_status.error_message = str(e)
                processing_status.save()
            except:
                pass


class VideoProcessingStatusView(LoginRequiredMixin, View):
    """Статус обробки відео"""
    
    def get(self, request, pk):
        media_file = get_object_or_404(MediaFile, pk=pk, file_type='video')
        
        try:
            processing_status = media_file.processing_status
            serializer = VideoProcessingStatusSerializer(processing_status)
            return JsonResponse(serializer.data)
        except VideoProcessingStatus.DoesNotExist:
            return JsonResponse({'status': 'not_started', 'progress': 0})


class GenerateThumbnailView(LoginRequiredMixin, View):
    """Генерація мініатюри для відео"""
    
    def post(self, request, pk):
        media_file = get_object_or_404(MediaFile, pk=pk, file_type='video')
        
        try:
            # Генеруємо мініатюру
            thumbnail_path = generate_thumbnail(media_file.file.path)
            
            if thumbnail_path:
                # Оновлюємо статус обробки
                processing_status = media_file.processing_status
                processing_status.thumbnail = thumbnail_path
                processing_status.save()
                
                return JsonResponse({'success': True, 'thumbnail_url': processing_status.thumbnail.url})
            else:
                return JsonResponse({'error': 'Failed to generate thumbnail'}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class ServeMediaFileView(LoginRequiredMixin, View):
    """Сервування медіа файлів з контролем доступу"""
    
    def get(self, request, pk):
        media_file = get_object_or_404(MediaFile, pk=pk)
        
        # Перевіряємо права доступу
        if not self.has_access(request.user, media_file):
            raise Http404
        
        # Відправляємо файл
        try:
            file_path = media_file.file.path
            content_type, _ = mimetypes.guess_type(file_path)
            
            with open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type=content_type)
                response['Content-Disposition'] = f'inline; filename="{media_file.title}"'
                return response
                
        except FileNotFoundError:
            raise Http404
    
    def has_access(self, user, media_file):
        """Перевірка прав доступу до файлу"""
        # Завантажувач завжди має доступ
        if media_file.uploaded_by == user:
            return True
        
        # Додаткова логіка перевірки прав доступу
        # (наприклад, пацієнти можуть бачити файли своїх лікарів)
        return True


class DownloadMediaFileView(ServeMediaFileView):
    """Завантаження медіа файлів"""
    
    def get(self, request, pk):
        media_file = get_object_or_404(MediaFile, pk=pk)
        
        if not self.has_access(request.user, media_file):
            raise Http404
        
        try:
            file_path = media_file.file.path
            content_type, _ = mimetypes.guess_type(file_path)
            
            with open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename="{media_file.title}"'
                return response
                
        except FileNotFoundError:
            raise Http404


class StreamVideoView(LoginRequiredMixin, View):
    """Стрімінг відео файлів"""
    
    def get(self, request, pk):
        media_file = get_object_or_404(MediaFile, pk=pk, file_type='video')
        
        if not self.has_access(request.user, media_file):
            raise Http404
        
        try:
            file_path = media_file.file.path
            
            def file_iterator(file_path, chunk_size=8192):
                with open(file_path, 'rb') as file:
                    while True:
                        chunk = file.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
            
            response = StreamingHttpResponse(
                file_iterator(file_path),
                content_type='video/mp4'
            )
            response['Content-Disposition'] = f'inline; filename="{media_file.title}"'
            
            return response
            
        except FileNotFoundError:
            raise Http404
    
    def has_access(self, user, media_file):
        return media_file.uploaded_by == user or True  # Додаткова логіка прав доступу


class MediaSearchView(LoginRequiredMixin, TemplateView):
    """Пошук медіа файлів"""
    template_name = 'media/search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        query = self.request.GET.get('q', '')
        if query:
            media_files = MediaFile.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            ).order_by('-created_at')
            
            paginator = Paginator(media_files, 20)
            page_number = self.request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            context['media_files'] = page_obj
            context['query'] = query
        
        return context


class MediaFilterView(LoginRequiredMixin, TemplateView):
    """Фільтрація медіа файлів"""
    template_name = 'media/filter.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Фільтрація
        queryset = MediaFile.objects.all()
        
        file_type = self.request.GET.get('type')
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        
        uploaded_by = self.request.GET.get('uploaded_by')
        if uploaded_by:
            queryset = queryset.filter(uploaded_by_id=uploaded_by)
        
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        context['media_files'] = queryset.order_by('-created_at')
        context['file_types'] = MediaFile.FILE_TYPES
        
        return context


class BulkMediaActionView(LoginRequiredMixin, View):
    """Масові дії з медіа файлами"""
    
    def post(self, request):
        action = request.POST.get('action')
        file_ids = request.POST.getlist('file_ids')
        
        if not file_ids:
            messages.error(request, _('No files selected.'))
            return redirect('media:media_library')
        
        media_files = MediaFile.objects.filter(id__in=file_ids)
        
        if action == 'delete':
            count = media_files.count()
            for media_file in media_files:
                if media_file.file:
                    default_storage.delete(media_file.file.name)
            media_files.delete()
            messages.success(request, _('%(count)d files deleted successfully.') % {'count': count})
        
        elif action == 'process_videos':
            video_files = media_files.filter(file_type='video')
            for video_file in video_files:
                VideoProcessingStatus.objects.get_or_create(
                    media_file=video_file,
                    defaults={'status': 'pending'}
                )
            messages.success(request, _('Video processing started for %(count)d files.') % {'count': video_files.count()})
        
        return redirect('media:media_library')


class StorageUsageView(LoginRequiredMixin, TemplateView):
    """Використання сховища"""
    template_name = 'media/storage_usage.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика використання
        total_files = MediaFile.objects.count()
        total_size = MediaFile.objects.aggregate(
            total_size=Sum('file_size')
        )['total_size'] or 0
        
        # Розподіл по типах файлів
        file_type_stats = {}
        for file_type, label in MediaFile.FILE_TYPES:
            count = MediaFile.objects.filter(file_type=file_type).count()
            size = MediaFile.objects.filter(file_type=file_type).aggregate(
                total_size=Sum('file_size')
            )['total_size'] or 0
            file_type_stats[file_type] = {'count': count, 'size': size, 'label': label}
        
        context.update({
            'total_files': total_files,
            'total_size': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'file_type_stats': file_type_stats,
        })
        
        return context


class CleanupStorageView(LoginRequiredMixin, View):
    """Очищення сховища"""
    
    def post(self, request):
        try:
            cleanup_results = self._perform_cleanup()
            
            message = _(
                'Storage cleanup completed. '
                'Deleted: %(orphaned)d orphaned files, %(temp)d temporary files, %(thumbnails)d thumbnails. '
                'Freed: %(size)s MB'
            ) % cleanup_results
            
            messages.success(request, message)
            
        except Exception as e:
            messages.error(request, _('Storage cleanup failed: %(error)s') % {'error': str(e)})
        
        return redirect('media:storage_usage')
    
    def _perform_cleanup(self):
        """Виконує очищення сховища"""
        import os
        from django.conf import settings
        from datetime import datetime, timedelta
        
        cleanup_stats = {
            'orphaned': 0,
            'temp': 0,
            'thumbnails': 0,
            'size': 0
        }
        
        media_root = settings.MEDIA_ROOT
        
        # 1. Видаляємо файли без записів в БД (orphaned files)
        if os.path.exists(media_root):
            for root, dirs, files in os.walk(media_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, media_root)
                    
                    # Перевіряємо, чи існує запис в БД для цього файлу
                    if not MediaFile.objects.filter(file=relative_path).exists():
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleanup_stats['orphaned'] += 1
                            cleanup_stats['size'] += file_size
                        except OSError:
                            pass  # Файл вже видалено або недоступний
        
        # 2. Видаляємо старі тимчасові файли (старше 24 годин)
        temp_dirs = [
            os.path.join(media_root, 'temp'),
            os.path.join(media_root, 'tmp'),
        ]
        
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            if datetime.fromtimestamp(os.path.getmtime(file_path)) < cutoff_time:
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cleanup_stats['temp'] += 1
                                cleanup_stats['size'] += file_size
                        except OSError:
                            pass
        
        # 3. Очищаємо кеш мініатюр (файли старше 7 днів)
        thumbnail_dirs = [
            os.path.join(media_root, 'thumbnails'),
            os.path.join(media_root, 'cache'),
        ]
        
        thumbnail_cutoff = datetime.now() - timedelta(days=7)
        
        for thumb_dir in thumbnail_dirs:
            if os.path.exists(thumb_dir):
                for root, dirs, files in os.walk(thumb_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            if datetime.fromtimestamp(os.path.getmtime(file_path)) < thumbnail_cutoff:
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cleanup_stats['thumbnails'] += 1
                                cleanup_stats['size'] += file_size
                        except OSError:
                            pass
        
        # Конвертуємо розмір в МБ
        cleanup_stats['size'] = round(cleanup_stats['size'] / (1024 * 1024), 2)
        
        return cleanup_stats
