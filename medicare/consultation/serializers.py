from rest_framework import serializers
from .models import Consultation, ConsultationNote, ConsultationRecording
from patients.serializers import PatientProfileLightSerializer
from staff.serializers import StaffProfileLightSerializer


class ConsultationNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationNote
        fields = ['id', 'consultation', 'content', 'created_at', 'updated_at']


class ConsultationRecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationRecording
        fields = ['id', 'consultation', 'file', 'duration', 'created_at']


class ConsultationSerializer(serializers.ModelSerializer):
    patient = PatientProfileLightSerializer(read_only=True)
    doctor = StaffProfileLightSerializer(read_only=True)
    consultation_note = ConsultationNoteSerializer(read_only=True, required=False)
    recording = ConsultationRecordingSerializer(read_only=True, required=False)

    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Consultation
        fields = [
            'id', 'patient', 'doctor', 'start_time', 'end_time', 'status',
            'consultation_type', 'video_link', 'notes', 'created_at', 'updated_at',
            'consultation_note', 'recording', 'patient_id', 'doctor_id'
        ]
        
    def validate(self, data):
        """
        Check that start is before end.
        """
        if 'start_time' in data and 'end_time' in data and data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must occur after start time")
        return data


class ConsultationLightSerializer(serializers.ModelSerializer):
    """A light serializer for lists and calendars."""
    patient = PatientProfileLightSerializer(read_only=True)
    doctor = StaffProfileLightSerializer(read_only=True)

    class Meta:
        model = Consultation
        fields = ['id', 'patient', 'doctor', 'start_time', 'end_time', 'status', 'consultation_type'] 