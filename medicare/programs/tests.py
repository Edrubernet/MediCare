from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import RehabilitationProgram
from patients.models import PatientProfile
from staff.models import StaffProfile
from exercises.models import Exercise
from datetime import date, timedelta

User = get_user_model()

class ProgramAPITests(APITestCase):

    def setUp(self):
        # Створення користувачів: лікар та два пацієнти
        self.doctor_user = User.objects.create_user(username='doctor', password='password123', user_type='doctor')
        self.patient_user_1 = User.objects.create_user(username='patient1', password='password123', user_type='patient')
        self.patient_user_2 = User.objects.create_user(username='patient2', password='password123', user_type='patient')

        # Створення профілів
        self.doctor_profile = StaffProfile.objects.create(user=self.doctor_user, specialization='Rehabilitation')
        self.patient_profile_1 = PatientProfile.objects.create(user=self.patient_user_1)
        self.patient_profile_2 = PatientProfile.objects.create(user=self.patient_user_2)

        # Створення тестової вправи
        self.exercise = Exercise.objects.create(title='Test Exercise', description='A simple test exercise')

        # Призначення пацієнта 1 лікарю
        self.doctor_profile.patients.add(self.patient_profile_1)

        self.program_url = reverse('rehabilitationprogram-list')

        # Створюємо базові дані для програми
        self.program_data = {
            'title': 'Test Program',
            'description': 'A program for testing.',
            'start_date': date.today().isoformat(),
            'end_date': (date.today() + timedelta(days=30)).isoformat(),
            'patient_id': self.patient_profile_1.id,
            'doctor_id': self.doctor_profile.id,
            'program_days': [
                {
                    'day_number': 1,
                    'exercises': [
                        {
                            'exercise': self.exercise.id,
                            'sets': 3,
                            'repetitions': 10
                        }
                    ]
                }
            ]
        }

    def test_doctor_can_create_program_for_assigned_patient(self):
        """
        Лікар повинен мати можливість створювати програму для свого пацієнта.
        """
        self.client.force_authenticate(user=self.doctor_user)
        
        response = self.client.post(self.program_url, self.program_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(RehabilitationProgram.objects.count(), 1)
        self.assertEqual(RehabilitationProgram.objects.get().title, 'Test Program')

    def test_doctor_cannot_create_program_for_unassigned_patient(self):
        """
        Лікар не повинен мати можливість створювати програму для чужого пацієнта.
        """
        self.client.force_authenticate(user=self.doctor_user)
        
        # Змінюємо ID пацієнта на не призначеного
        data = self.program_data.copy()
        data['patient_id'] = self.patient_profile_2.id
        
        response = self.client.post(self.program_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_cannot_create_program(self):
        """
        Пацієнт не повинен мати можливість створювати програми.
        """
        self.client.force_authenticate(user=self.patient_user_1)
        
        response = self.client.post(self.program_url, self.program_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_create_program(self):
        """
        Неавтентифікований користувач не може створювати програми.
        """
        response = self.client.post(self.program_url, self.program_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
