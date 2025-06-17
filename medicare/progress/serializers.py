from rest_framework import serializers
from .models import ExerciseSession, ExerciseCompletion, PatientNote, RehabilitationGoal, GoalProgress
from programs.serializers import RehabilitationProgramLightSerializer
from patients.serializers import PatientProfileLightSerializer


class ExerciseCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseCompletion
        fields = [
            'id', 'program_exercise', 'sets_completed', 'repetitions_completed',
            'pain_level', 'difficulty_level', 'notes', 'completed_at'
        ]


class ExerciseSessionSerializer(serializers.ModelSerializer):
    completions = ExerciseCompletionSerializer(many=True, source='exercise_completions')
    patient = PatientProfileLightSerializer(read_only=True)
    program = RehabilitationProgramLightSerializer(read_only=True)
    
    patient_id = serializers.IntegerField(write_only=True)
    program_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ExerciseSession
        fields = [
            'id', 'program', 'patient', 'date', 'completed', 'notes',
            'created_at', 'completions', 'patient_id', 'program_id'
        ]



class PatientNoteSerializer(serializers.ModelSerializer):
    patient = PatientProfileLightSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    
    class Meta:
        model = PatientNote
        fields = ['id', 'patient', 'doctor', 'doctor_name', 'note', 'created_at', 'patient_id']
        read_only_fields = ['doctor']


class GoalProgressSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source='recorded_by.user.get_full_name', read_only=True)
    
    class Meta:
        model = GoalProgress
        fields = ['id', 'value', 'notes', 'recorded_by', 'recorded_by_name', 'recorded_at']
        read_only_fields = ['recorded_by']


class RehabilitationGoalSerializer(serializers.ModelSerializer):
    patient = PatientProfileLightSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    doctor_name = serializers.CharField(source='doctor.user.get_full_name', read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    progress_entries = GoalProgressSerializer(many=True, read_only=True)
    
    class Meta:
        model = RehabilitationGoal
        fields = [
            'id', 'patient', 'patient_id', 'doctor', 'doctor_name', 'title', 'description',
            'category', 'priority', 'current_value', 'target_value', 'unit',
            'target_date', 'created_at', 'updated_at', 'is_achieved', 'achieved_at',
            'progress_percentage', 'progress_entries'
        ]
        read_only_fields = ['doctor', 'is_achieved', 'achieved_at']


class RehabilitationGoalLightSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = RehabilitationGoal
        fields = [
            'id', 'title', 'category', 'priority', 'current_value', 'target_value',
            'target_date', 'is_achieved', 'progress_percentage'
        ] 