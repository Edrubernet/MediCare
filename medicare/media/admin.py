from django.contrib import admin
from .models import MediaFile, VideoProcessingStatus


class VideoProcessingStatusInline(admin.StackedInline):
    model = VideoProcessingStatus
    can_delete = False
    extra = 0
    readonly_fields = ('started_at', 'completed_at')


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_type', 'get_file_size_mb', 'uploaded_by', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('title', 'description', 'uploaded_by__first_name', 'uploaded_by__last_name')
    inlines = [VideoProcessingStatusInline]
    readonly_fields = ('file_size', 'mime_type', 'created_at')
    date_hierarchy = 'created_at'
    
    def get_file_size_mb(self, obj):
        return f"{obj.file_size / (1024 * 1024):.2f} MB"
    get_file_size_mb.short_description = 'File Size'


@admin.register(VideoProcessingStatus)
class VideoProcessingStatusAdmin(admin.ModelAdmin):
    list_display = ('media_file', 'status', 'progress', 'duration', 'resolution', 'completed_at')
    list_filter = ('status', 'started_at', 'completed_at')
    search_fields = ('media_file__title',)
    readonly_fields = ('started_at', 'completed_at')
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == 'completed':
            return self.readonly_fields + ('status', 'progress')
        return self.readonly_fields
