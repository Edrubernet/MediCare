from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, StaffProfile, Certificate, WorkSchedule
from patients.models import PatientProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'patronymic', 'user_type', 
                  'phone_number', 'profile_image']
        read_only_fields = ['id', 'username']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class CertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = ['id', 'name', 'description', 'file', 'issue_date']


class WorkScheduleSerializer(serializers.ModelSerializer):
    day_of_week_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = WorkSchedule
        fields = ['id', 'staff', 'day_of_week', 'day_of_week_name', 'start_time', 'end_time']


class PatientListSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = PatientProfile
        fields = ['id', 'user', 'user_full_name']


class StaffProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    certificates = CertificateSerializer(many=True, read_only=True)
    work_schedules = WorkScheduleSerializer(many=True, read_only=True)
    patients = PatientListSerializer(many=True, read_only=True)
    
    class Meta:
        model = StaffProfile
        fields = ['id', 'user', 'specialization', 'bio', 'certificates', 'work_schedules', 'patients']
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['user_type'] = 'doctor'  # Встановлюємо тип користувача як лікар
        
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        
        staff_profile = StaffProfile.objects.create(user=user, **validated_data)
        return staff_profile


class StaffProfileLightSerializer(serializers.ModelSerializer):
    """Легка версія серіалізатора для вкладених відносин"""
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = StaffProfile
        fields = ['id', 'full_name', 'specialization']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    user_type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True)
    patronymic = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'patronymic', 'user_type')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }

    def create(self, validated_data):
        user_type = validated_data.pop('user_type')
        
        # Generate username automatically from email
        username = validated_data['email'].split('@')[0]
        # Ensure username is unique
        if User.objects.filter(username=username).exists():
            username = f"{username}_{User.objects.count()}"

        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            patronymic=validated_data.get('patronymic', ''),
            user_type=user_type
        )

        # Create a profile based on user type
        if user_type == 'doctor':
            StaffProfile.objects.create(user=user)
        elif user_type == 'patient':
            PatientProfile.objects.create(user=user)

        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims to the token
        token['username'] = user.username
        token['email'] = user.email
        token['user_type'] = user.user_type
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['patronymic'] = user.patronymic

        return token


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    
    class Meta:
        from programs.models import Appointment
        model = Appointment
        fields = [
            'id', 'doctor', 'doctor_name', 'patient', 'patient_name', 'date', 
            'start_time', 'end_time', 'status', 'appointment_type', 'description', 
            'notes', 'duration_minutes', 'created_at', 'updated_at'
        ]