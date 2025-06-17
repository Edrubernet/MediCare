from rest_framework import serializers
from django.db import transaction
from .models import RehabilitationProgram, ProgramDay, ProgramExercise, Appointment
from patients.serializers import PatientProfileLightSerializer
from staff.serializers import StaffProfileLightSerializer
from exercises.serializers import ExerciseLightSerializer
from exercises.models import Exercise


class ProgramExerciseSerializer(serializers.ModelSerializer):
    """Serializer for an exercise within a program day."""
    exercise_details = ExerciseLightSerializer(source='exercise', read_only=True)
    exercise = serializers.PrimaryKeyRelatedField(
        queryset=Exercise.objects.all(), write_only=True
    )

    class Meta:
        model = ProgramExercise
        fields = [
            'id', 'exercise', 'exercise_details', 'sets', 'repetitions',
            'duration', 'rest_between_sets', 'order', 'additional_instructions'
        ]


class ProgramDaySerializer(serializers.ModelSerializer):
    """Serializer for a day within a rehabilitation program."""
    exercises = ProgramExerciseSerializer(many=True)

    class Meta:
        model = ProgramDay
        fields = ['id', 'day_number', 'notes', 'exercises']


class RehabilitationProgramSerializer(serializers.ModelSerializer):
    """Serializer for a full rehabilitation program."""
    program_days = ProgramDaySerializer(many=True)
    patient = PatientProfileLightSerializer(read_only=True)
    doctor = StaffProfileLightSerializer(read_only=True)
    
    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = RehabilitationProgram
        fields = [
            'id', 'title', 'description', 'status', 'start_date', 'end_date',
            'created_at', 'updated_at', 'patient', 'doctor', 'program_days',
            'patient_id', 'doctor_id'
        ]

    @transaction.atomic
    def create(self, validated_data):
        program_days_data = validated_data.pop('program_days')
        
        program = RehabilitationProgram.objects.create(**validated_data)

        for day_data in program_days_data:
            exercises_data = day_data.pop('exercises')
            day = ProgramDay.objects.create(program=program, **day_data)
            for exercise_data in exercises_data:
                ProgramExercise.objects.create(program_day=day, **exercise_data)

        return program

    @transaction.atomic
    def update(self, instance, validated_data):
        program_days_data = validated_data.pop('program_days', None)

        # Update flat fields of the program
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.status = validated_data.get('status', instance.status)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.end_date = validated_data.get('end_date', instance.end_date)
        instance.save()

        if program_days_data is not None:
            # Clear existing days and exercises and recreate them
            instance.program_days.all().delete()
            for day_data in program_days_data:
                exercises_data = day_data.pop('exercises')
                day = ProgramDay.objects.create(program=instance, **day_data)
                for exercise_data in exercises_data:
                    ProgramExercise.objects.create(program_day=day, **exercise_data)
        
        return instance


class RehabilitationProgramLightSerializer(serializers.ModelSerializer):
    """A light serializer for lists."""
    patient = PatientProfileLightSerializer(read_only=True)
    doctor = StaffProfileLightSerializer(read_only=True)

    class Meta:
        model = RehabilitationProgram
        fields = ['id', 'title', 'patient', 'doctor', 'status', 'start_date', 'end_date']


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for appointments."""
    patient = PatientProfileLightSerializer(read_only=True)
    doctor = StaffProfileLightSerializer(read_only=True)
    
    patient_id = serializers.IntegerField(write_only=True)
    doctor_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'doctor', 'appointment_type', 'date', 'start_time', 
            'end_time', 'status', 'description', 'notes', 'related_program',
            'reminder_sent', 'created_at', 'updated_at', 'patient_id', 'doctor_id'
        ]
        read_only_fields = ['created_at', 'updated_at', 'reminder_sent'] 