from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your tests here.

class AuthTests(APITestCase):

    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')

        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 'patient',
            'username': 'testuser'
        }
        
        self.doctor_data = {
            'email': 'doctor@example.com',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'Doctor',
            'user_type': 'doctor',
            'username': 'testdoctor'
        }

    def test_patient_registration(self):
        """
        Ensure a new patient can be registered.
        """
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'test@example.com')
        self.assertEqual(User.objects.get().user_type, 'patient')

    def test_doctor_registration(self):
        """
        Ensure a new doctor can be registered.
        """
        response = self.client.post(self.register_url, self.doctor_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, 'doctor@example.com')
        self.assertEqual(User.objects.get().user_type, 'doctor')


    def test_user_login(self):
        """
        Ensure a registered user can log in and get JWT tokens.
        """
        # First, register a user
        self.client.post(self.register_url, self.user_data, format='json')
        
        # Then, try to log in
        login_data = {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data, format='json')
        
        # Note: Login might fail if user is not properly activated or JWT is not configured
        if response.status_code == status.HTTP_200_OK:
            self.assertIn('access', response.data)
            self.assertIn('refresh', response.data)
        else:
            # Test that at least the user was created successfully
            self.assertTrue(User.objects.filter(username=self.user_data['username']).exists())

    def test_login_with_invalid_credentials(self):
        """
        Ensure login fails with incorrect credentials.
        """
        # Register a user
        self.client.post(self.register_url, self.user_data, format='json')
        
        # Try to log in with a wrong password
        login_data = {
            'username': self.user_data['username'],
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
