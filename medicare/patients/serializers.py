from rest_framework import serializers
from .models import PatientProfile, MedicalHistory, RehabilitationHistory
from staff.models import User
from staff.serializers import UserSerializer, StaffProfileLightSerializer


class PatientSearchSerializer(serializers.ModelSerializer):
    """
    Serializer for returning basic user info in patient search results.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    profile_id = serializers.IntegerField(source='patient_profile.id', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'profile_id', 'full_name', 'email']


class MedicalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalHistory
        fields = ['id', 'patient', 'conditions', 'allergies', 'medications', 'surgeries', 'family_history']


class RehabilitationHistorySerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    
    class Meta:
        model = RehabilitationHistory
        fields = ['id', 'patient', 'injury_type', 'injury_date', 'diagnosis', 'notes', 
                  'doctor', 'doctor_name', 'created_at', 'updated_at']


class PatientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    medical_history = MedicalHistorySerializer(read_only=True)
    rehabilitation_history = RehabilitationHistorySerializer(many=True, read_only=True)
    assigned_doctors = StaffProfileLightSerializer(many=True, read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    
    class Meta:
        model = PatientProfile
        fields = ['id', 'user', 'date_of_birth', 'gender', 'gender_display', 'address', 
                  'emergency_contact_name', 'emergency_contact_phone', 
                  'assigned_doctors', 'medical_history', 'rehabilitation_history']
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['user_type'] = 'patient'  # Встановлюємо тип користувача як пацієнт
        
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        
        patient_profile = PatientProfile.objects.create(user=user, **validated_data)
        return patient_profile


class PatientProfileLightSerializer(serializers.ModelSerializer):
    """Легка версія серіалізатора для вкладених відносин"""
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = PatientProfile
        fields = ['id', 'full_name', 'gender']