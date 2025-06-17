from rest_framework import serializers
from .models import MediaFile, VideoProcessingStatus


class MediaFileSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MediaFile
        fields = [
            'id', 'title', 'description', 'file', 'file_url', 'file_type', 
            'file_size', 'file_size_mb', 'mime_type', 'uploaded_by', 
            'uploaded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'file_size', 'mime_type', 'created_at']
    
    def get_file_size_mb(self, obj):
        return round(obj.file_size / (1024 * 1024), 2) if obj.file_size else 0
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class VideoProcessingStatusSerializer(serializers.ModelSerializer):
    media_file_title = serializers.CharField(source='media_file.title', read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    processed_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = VideoProcessingStatus
        fields = [
            'id', 'media_file', 'media_file_title', 'status', 'progress', 
            'error_message', 'processed_file', 'processed_file_url', 
            'thumbnail', 'thumbnail_url', 'duration', 'resolution',
            'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at']
    
    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None
    
    def get_processed_file_url(self, obj):
        request = self.context.get('request')
        if obj.processed_file and request:
            return request.build_absolute_uri(obj.processed_file.url)
        return None