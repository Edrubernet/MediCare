from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import (
    BodyPart, ExerciseCategory, DifficultyLevel, Exercise, 
    ExerciseImage, EducationalMaterial
)

User = get_user_model()


class ExerciseModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testdoctor',
            email='doctor@test.com',
            user_type='doctor'
        )
        self.body_part = BodyPart.objects.create(name='Test Body Part')
        self.category = ExerciseCategory.objects.create(
            name='Test Category',
            description='Test Description'
        )
        self.difficulty = DifficultyLevel.objects.create(
            name='Beginner',
            value=1
        )
        
    def test_body_part_creation(self):
        self.assertEqual(str(self.body_part), 'Test Body Part')
        
    def test_exercise_category_creation(self):
        self.assertEqual(str(self.category), 'Test Category')
        
    def test_difficulty_level_creation(self):
        self.assertEqual(str(self.difficulty), 'Beginner')
        self.assertEqual(self.difficulty.value, 1)
        
    def test_exercise_creation(self):
        exercise = Exercise.objects.create(
            title='Test Exercise',
            description='Test Description',
            instructions='Test Instructions',
            difficulty=self.difficulty,
            created_by=self.user
        )
        exercise.body_parts.add(self.body_part)
        exercise.categories.add(self.category)
        
        self.assertEqual(str(exercise), 'Test Exercise')
        self.assertEqual(exercise.body_parts.count(), 1)
        self.assertEqual(exercise.categories.count(), 1)
        
    def test_educational_material_creation(self):
        material = EducationalMaterial.objects.create(
            title='Test Material',
            description='Test Description',
            file_type='pdf',
            created_by=self.user
        )
        self.assertEqual(str(material), 'Test Material')


class ExerciseViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testdoctor',
            email='doctor@test.com',
            password='testpass123',
            user_type='doctor'
        )
        
    def test_exercise_list_access(self):
        self.client.login(username='testdoctor', password='testpass123')
        response = self.client.get('/exercises/')
        self.assertEqual(response.status_code, 200)
