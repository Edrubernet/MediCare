from rest_framework import serializers
from .models import Report, ReportExport


class ReportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    exports_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            'id', 'title', 'report_type', 'report_type_display', 'description', 
            'parameters', 'created_by', 'created_by_name', 'created_at',
            'exports_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']
    
    def get_exports_count(self, obj):
        return obj.exports.count()
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ReportExportSerializer(serializers.ModelSerializer):
    report_title = serializers.CharField(source='report.title', read_only=True)
    file_url = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportExport
        fields = [
            'id', 'report', 'report_title', 'file', 'file_url', 
            'file_size', 'format', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def get_file_size(self, obj):
        try:
            return obj.file.size if obj.file else 0
        except:
            return 0


class ReportParametersSerializer(serializers.Serializer):
    """Серіалізатор для параметрів звітів"""
    
    # Загальні параметри
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    
    # Параметри для звітів по пацієнтах
    patient_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    
    # Параметри для звітів по програмах
    program_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    
    # Параметри для звітів по лікарях
    doctor_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    
    # Параметри для звітів по опитуванням
    survey_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    
    # Додаткові фільтри
    include_inactive = serializers.BooleanField(default=False)
    group_by_period = serializers.ChoiceField(
        choices=['day', 'week', 'month', 'year'],
        default='month',
        required=False
    )
    
    def validate(self, data):
        """Валідація параметрів"""
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError(
                "date_from cannot be greater than date_to"
            )
        
        return data