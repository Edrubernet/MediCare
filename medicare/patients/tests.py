from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import PatientProfile, MedicalHistory, RehabilitationHistory

User = get_user_model()


class PatientProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testpatient',
            email='patient@test.com',
            first_name='Test',
            last_name='Patient',
            user_type='patient'
        )
        
    def test_patient_profile_creation(self):
        patient = PatientProfile.objects.create(
            user=self.user,
            gender='M',
            address='Test Address'
        )
        self.assertEqual(str(patient), 'Test Patient')
        self.assertEqual(patient.user.user_type, 'patient')
        
    def test_medical_history_creation(self):
        patient = PatientProfile.objects.create(user=self.user)
        medical_history = MedicalHistory.objects.create(
            patient=patient,
            conditions='Test conditions',
            allergies='Test allergies'
        )
        self.assertEqual(str(medical_history), "Test Patient's Medical History")
        
    def test_rehabilitation_history_creation(self):
        patient = PatientProfile.objects.create(user=self.user)
        rehab_history = RehabilitationHistory.objects.create(
            patient=patient,
            injury_type='Test Injury',
            injury_date='2024-01-01',
            diagnosis='Test diagnosis'
        )
        self.assertEqual(str(rehab_history), 'Test Patient - Test Injury')


class PatientViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpass123',
            user_type='patient'
        )
        self.patient = PatientProfile.objects.create(user=self.user)
        
    def test_patient_profile_access(self):
        self.client.login(username='testpatient', password='testpass123')
        response = self.client.get('/patients/')
        self.assertEqual(response.status_code, 200)
