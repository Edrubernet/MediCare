from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from patients.models import PatientProfile
from staff.models import StaffProfile

User = get_user_model()


class CoreViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            user_type='admin',
            is_staff=True
        )
        
        self.doctor_user = User.objects.create_user(
            username='testdoctor',
            email='doctor@test.com',
            password='testpass123',
            user_type='doctor'
        )
        
        self.patient_user = User.objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpass123',
            user_type='patient'
        )
        
        # Create profiles
        self.doctor_profile = StaffProfile.objects.create(
            user=self.doctor_user,
            specialization='Physical Therapy'
        )
        
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user
        )
        
    def test_home_page_anonymous(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
    def test_login_view_get(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
        
    def test_login_view_post_valid(self):
        response = self.client.post('/login/', {
            'username': 'testadmin',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        
    def test_login_view_post_invalid(self):
        response = self.client.post('/login/', {
            'username': 'wronguser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
        
    def test_admin_dashboard_access(self):
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get('/admin-dashboard/')
        self.assertEqual(response.status_code, 200)
        
    def test_therapist_dashboard_access(self):
        self.client.login(username='testdoctor', password='testpass123')
        response = self.client.get('/therapist-dashboard/')
        self.assertEqual(response.status_code, 200)
        
    def test_patient_dashboard_access(self):
        self.client.login(username='testpatient', password='testpass123')
        response = self.client.get('/patient-dashboard/')
        self.assertEqual(response.status_code, 200)
        
    def test_dashboard_redirect_unauthorized(self):
        # Test admin dashboard access by non-admin
        self.client.login(username='testpatient', password='testpass123')
        response = self.client.get('/admin-dashboard/')
        self.assertEqual(response.status_code, 302)  # Redirect
        
    def test_logout_view(self):
        self.client.login(username='testadmin', password='testpass123')
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 302)  # Redirect after logout


class LoginSecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            user_type='patient'
        )
        
    def test_failed_login_attempts_tracking(self):
        # Test multiple failed login attempts
        for i in range(3):
            response = self.client.post('/login/', {
                'username': 'testuser',
                'password': 'wrongpass'
            })
            self.assertEqual(response.status_code, 200)
            
        # Refresh user from database
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 3)
        
    def test_successful_login_resets_attempts(self):
        # First fail a few times
        for i in range(2):
            self.client.post('/login/', {
                'username': 'testuser',
                'password': 'wrongpass'
            })
            
        # Then succeed
        response = self.client.post('/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Check that attempts were reset
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertIsNone(self.user.account_locked_until)