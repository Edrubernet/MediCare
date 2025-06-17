import os
import mimetypes
import logging
import subprocess
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from PIL import Image

logger = logging.getLogger(__name__)


def get_file_type(file):
    """Визначає тип файлу на основі MIME типу"""
    mime_type = file.content_type
    
    if mime_type.startswith('video/'):
        return 'video'
    elif mime_type.startswith('image/'):
        return 'image'
    elif mime_type.startswith('audio/'):
        return 'audio'
    elif mime_type in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        return 'document'
    else:
        return 'document'  # За замовчуванням


def validate_file_size(file, max_size):
    """Перевірка розміру файлу"""
    return file.size <= max_size


def validate_file_type(file):
    """Перевірка типу файлу"""
    allowed_video_formats = getattr(settings, 'ALLOWED_VIDEO_FORMATS', 'mp4,avi,mov,wmv').split(',')
    allowed_image_formats = getattr(settings, 'ALLOWED_IMAGE_FORMATS', 'jpg,jpeg,png,gif,webp').split(',')
    allowed_audio_formats = getattr(settings, 'ALLOWED_AUDIO_FORMATS', 'mp3,wav,ogg').split(',')
    allowed_document_formats = getattr(settings, 'ALLOWED_DOCUMENT_FORMATS', 'pdf,doc,docx,txt').split(',')
    
    file_extension = file.name.split('.')[-1].lower() if '.' in file.name else ''
    
    all_allowed_formats = allowed_video_formats + allowed_image_formats + allowed_audio_formats + allowed_document_formats
    
    return file_extension in all_allowed_formats


def generate_thumbnail(video_path, output_path=None, time_offset=5):
    """Генерує мініатюру для відео файлу"""
    try:
        if not output_path:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(settings.MEDIA_ROOT, 'video_thumbnails', f'{base_name}_thumb.jpg')
        
        # Створюємо директорію якщо не існує
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Використовуємо ffmpeg для генерації мініатюри
        command = [
            'ffmpeg',
            '-i', video_path,
            '-ss', str(time_offset),
            '-vframes', '1',
            '-q:v', '2',
            '-y',  # Перезаписувати файл
            output_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Error generating thumbnail: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Exception generating thumbnail: {str(e)}")
        return None


def process_video_file(media_file_id):
    """Обробка відео файлу (для асинхронного виконання з Celery)"""
    try:
        from .models import MediaFile, VideoProcessingStatus
        
        media_file = MediaFile.objects.get(id=media_file_id)
        processing_status = media_file.processing_status
        
        # Оновлюємо статус
        processing_status.status = 'processing'
        processing_status.progress = 0
        processing_status.save()
        
        video_path = media_file.file.path
        
        # Отримуємо інформацію про відео
        duration, resolution = get_video_info(video_path)
        
        processing_status.progress = 25
        processing_status.duration = duration
        processing_status.resolution = resolution
        processing_status.save()
        
        # Генеруємо мініатюру
        thumbnail_path = generate_thumbnail(video_path)
        if thumbnail_path:
            processing_status.thumbnail = thumbnail_path
        
        processing_status.progress = 50
        processing_status.save()
        
        # Конвертуємо відео (якщо потрібно)
        processed_path = convert_video(video_path)
        if processed_path:
            processing_status.processed_file = processed_path
        
        processing_status.progress = 100
        processing_status.status = 'completed'
        processing_status.save()
        
        return True
        
    except Exception as e:
        processing_status.status = 'failed'
        processing_status.error_message = str(e)
        processing_status.save()
        return False


def get_video_info(video_path):
    """Отримує інформацію про відео файл"""
    try:
        # Використовуємо ffprobe для отримання інформації
        command = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout)
            
            duration = float(info['format']['duration'])
            
            # Знаходимо відео потік
            video_stream = None
            for stream in info['streams']:
                if stream['codec_type'] == 'video':
                    video_stream = stream
                    break
            
            if video_stream:
                width = video_stream.get('width', 0)
                height = video_stream.get('height', 0)
                resolution = f"{width}x{height}"
            else:
                resolution = "unknown"
            
            return int(duration), resolution
        
        return None, None
        
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        return None, None


def convert_video(input_path, output_path=None, target_format='mp4'):
    """Конвертує відео в заданий формат"""
    try:
        if not output_path:
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(settings.MEDIA_ROOT, 'processed_videos', f'{base_name}_processed.{target_format}')
        
        # Створюємо директорію якщо не існує
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Конвертуємо відео за допомогою ffmpeg
        command = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y',  # Перезаписувати файл
            output_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Error converting video: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Exception converting video: {str(e)}")
        return None


def resize_image(image_path, max_width=1920, max_height=1080, quality=85):
    """Зменшує розмір зображення"""
    try:
        with Image.open(image_path) as img:
            # Зберігаємо пропорції
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Зберігаємо оптимізоване зображення
            output_path = image_path.replace('.', '_optimized.')
            img.save(output_path, optimize=True, quality=quality)
            
            return output_path
            
    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}")
        return None


def clean_filename(filename):
    """Очищає ім'я файлу від небезпечних символів"""
    import re
    
    # Видаляємо небезпечні символи
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Обмежуємо довжину
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext