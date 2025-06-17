from rest_framework import serializers
from .models import GoogleCalendarCredentials, GoogleCalendarEvent


class GoogleCalendarCredentialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleCalendarCredentials
        fields = ['id', 'user', 'token_expiry', 'created_at', 'updated_at']
        read_only_fields = ['access_token', 'refresh_token']


class GoogleCalendarEventSerializer(serializers.ModelSerializer):
    consultation_title = serializers.CharField(source='consultation.title', read_only=True)
    consultation_id = serializers.IntegerField(source='consultation.id', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = GoogleCalendarEvent
        fields = [
            'id', 'user', 'user_name', 'google_event_id', 
            'consultation', 'consultation_id', 'consultation_title',
            'event_summary', 'event_description', 'start_time', 'end_time',
            'created_at', 'updated_at', 'last_synced'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'last_synced']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)