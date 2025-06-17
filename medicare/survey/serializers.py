from rest_framework import serializers
from .models import (
    Survey, Question, QuestionOption, SurveyAssignment, 
    SurveyResponse, QuestionResponse
)


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'text', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'text', 'question_type', 'question_type_display', 
            'required', 'order', 'options'
        ]


class SurveySerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    questions_count = serializers.SerializerMethodField()
    assignments_count = serializers.SerializerMethodField()
    responses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Survey
        fields = [
            'id', 'title', 'description', 'created_by', 'created_by_name',
            'is_active', 'created_at', 'updated_at', 'questions',
            'questions_count', 'assignments_count', 'responses_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_questions_count(self, obj):
        return obj.questions.count()
    
    def get_assignments_count(self, obj):
        return obj.assignments.count()
    
    def get_responses_count(self, obj):
        return SurveyResponse.objects.filter(
            assignment__survey=obj,
            completed_at__isnull=False
        ).count()
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class SurveyAssignmentSerializer(serializers.ModelSerializer):
    survey_title = serializers.CharField(source='survey.title', read_only=True)
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = SurveyAssignment
        fields = [
            'id', 'survey', 'survey_title', 'patient', 'patient_name',
            'assigned_by', 'assigned_by_name', 'status', 'status_display',
            'due_date', 'assigned_date', 'completed_date', 'is_overdue'
        ]
        read_only_fields = ['id', 'assigned_by', 'assigned_date', 'completed_date']
    
    def get_is_overdue(self, obj):
        if obj.due_date and obj.status == 'pending':
            from datetime import date
            return obj.due_date < date.today()
        return False
    
    def create(self, validated_data):
        validated_data['assigned_by'] = self.context['request'].user
        return super().create(validated_data)


class QuestionResponseSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    question_type = serializers.CharField(source='question.question_type', read_only=True)
    selected_options_text = serializers.SerializerMethodField()
    
    class Meta:
        model = QuestionResponse
        fields = [
            'id', 'question', 'question_text', 'question_type',
            'text_answer', 'selected_options', 'selected_options_text',
            'rating_answer'
        ]
    
    def get_selected_options_text(self, obj):
        return [option.text for option in obj.selected_options.all()]


class SurveyResponseSerializer(serializers.ModelSerializer):
    survey_title = serializers.CharField(source='assignment.survey.title', read_only=True)
    patient_name = serializers.CharField(source='assignment.patient.user.get_full_name', read_only=True)
    question_responses = QuestionResponseSerializer(many=True, read_only=True)
    completion_time_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = SurveyResponse
        fields = [
            'id', 'assignment', 'survey_title', 'patient_name',
            'started_at', 'completed_at', 'completion_time_minutes',
            'question_responses'
        ]
        read_only_fields = ['id', 'started_at']
    
    def get_completion_time_minutes(self, obj):
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return round(duration.total_seconds() / 60, 1)
        return None


class SurveyStatsSerializer(serializers.Serializer):
    """Серіалізатор для статистики опитування"""
    total_assignments = serializers.IntegerField()
    completed_responses = serializers.IntegerField()
    pending_assignments = serializers.IntegerField()
    expired_assignments = serializers.IntegerField()
    completion_rate = serializers.FloatField()
    average_completion_time = serializers.FloatField()
    
    # Статистика по типах питань
    text_questions_count = serializers.IntegerField()
    rating_questions_count = serializers.IntegerField()
    choice_questions_count = serializers.IntegerField()
    
    # Останні відповіді
    recent_completions = serializers.ListField(child=serializers.DictField())


class QuestionAnalyticsSerializer(serializers.Serializer):
    """Серіалізатор для аналітики питання"""
    question_id = serializers.IntegerField()
    question_text = serializers.CharField()
    question_type = serializers.CharField()
    responses_count = serializers.IntegerField()
    
    # Статистика для різних типів питань
    average_rating = serializers.FloatField(required=False)
    rating_distribution = serializers.DictField(required=False)
    
    yes_percentage = serializers.FloatField(required=False)
    no_percentage = serializers.FloatField(required=False)
    
    option_counts = serializers.DictField(required=False)
    option_percentages = serializers.DictField(required=False)
    
    # Найпопулярніші текстові відповіді
    common_answers = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )