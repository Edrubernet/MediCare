from rest_framework import serializers
from .models import (
    BodyPart, ExerciseCategory, DifficultyLevel, Exercise,
    ExerciseImage, EducationalMaterial
)
from staff.serializers import UserSerializer


class BodyPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyPart
        fields = ['id', 'name']


class ExerciseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseCategory
        fields = ['id', 'name', 'description']


class DifficultyLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DifficultyLevel
        fields = ['id', 'name', 'value']


class ExerciseImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseImage
        fields = ['id', 'image', 'caption']


class ExerciseSerializer(serializers.ModelSerializer):
    body_parts = BodyPartSerializer(many=True, read_only=True)
    categories = ExerciseCategorySerializer(many=True, read_only=True)
    difficulty = DifficultyLevelSerializer(read_only=True)
    images = ExerciseImageSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Exercise
        fields = [
            'id', 'title', 'description', 'instructions', 'precautions',
            'video', 'video_thumbnail', 'difficulty', 'body_parts',
            'categories', 'images', 'is_public', 'created_by',
            'created_at', 'updated_at'
        ]


class ExerciseLightSerializer(serializers.ModelSerializer):
    """A light serializer for use in program definitions."""
    class Meta:
        model = Exercise
        fields = ['id', 'title', 'video', 'video_thumbnail']


class EducationalMaterialSerializer(serializers.ModelSerializer):
    related_exercises = ExerciseLightSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = EducationalMaterial
        fields = [
            'id', 'title', 'description', 'file', 'file_type',
            'related_exercises', 'created_by', 'created_at'
        ] 