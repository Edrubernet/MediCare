"""
Тести безпеки для системи реабілітації
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages import get_messages
from unittest.mock import patch
import json

from patients.models import PatientProfile
from staff.models import StaffProfile

User = get_user_model()


class SecurityTestCase(TestCase):
    """Базовий клас для тестів безпеки"""
    
    def setUp(self):
        self.client = Client()
        
        # Створюємо тестових користувачів
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='admin123',
            user_type='admin',
            first_name='Admin',
            last_name='User'
        )
        
        self.doctor_user = User.objects.create_user(
            username='doctor_test',
            email='doctor@test.com',
            password='doctor123',
            user_type='doctor',
            first_name='Doctor',
            last_name='Smith'
        )
        
        self.patient_user = User.objects.create_user(
            username='patient_test',
            email='patient@test.com',
            password='patient123',
            user_type='patient',
            first_name='Patient',
            last_name='Doe'
        )
        
        self.other_patient_user = User.objects.create_user(
            username='patient2_test',
            email='patient2@test.com',
            password='patient123',
            user_type='patient',
            first_name='Other',
            last_name='Patient'
        )
        
        # Створюємо профілі
        self.doctor_profile = StaffProfile.objects.create(
            user=self.doctor_user,
            specialization='Фізіотерапевт'
        )
        
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient_user,
            gender='M',
            emergency_contact_name='Emergency Contact',
            emergency_contact_phone='+380501234567'
        )
        
        self.other_patient_profile = PatientProfile.objects.create(
            user=self.other_patient_user,
            gender='F',
            emergency_contact_name='Other Emergency',
            emergency_contact_phone='+380507654321'
        )
        
        # Призначаємо лікаря пацієнту
        self.patient_profile.assigned_doctors.add(self.doctor_profile)


class AccessControlTests(SecurityTestCase):
    """Тести контролю доступу"""
    
    def test_unauthenticated_access_redirects_to_login(self):
        """Неавтентифіковані користувачі перенаправляються на сторінку входу"""
        protected_urls = [
            reverse('core:dashboard'),
            reverse('patients:patient_list'),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            self.assertRedirects(response, f'/auth/login/?next={url}')
    
    def test_patient_cannot_access_patient_list(self):
        """Пацієнти не можуть бачити список інших пацієнтів"""
        self.client.login(username='patient_test', password='patient123')
        response = self.client.get(reverse('patients:patient_list'))
        
        # Повинно перенаправляти або повертати 403
        self.assertIn(response.status_code, [302, 403])
        
        if response.status_code == 302:
            messages = list(get_messages(response.wsgi_request))
            self.assertTrue(any('немає дозволу' in str(m) for m in messages))
    
    def test_doctor_can_only_see_assigned_patients(self):
        """Лікарі бачать тільки призначених їм пацієнтів"""
        self.client.login(username='doctor_test', password='doctor123')
        response = self.client.get(reverse('patients:patient_list'))
        
        self.assertEqual(response.status_code, 200)
        # Перевіряємо, що в контексті тільки призначені пацієнти
        patients = response.context['patients']
        patient_ids = [p.id for p in patients]
        
        self.assertIn(self.patient_profile.id, patient_ids)
        self.assertNotIn(self.other_patient_profile.id, patient_ids)
    
    def test_doctor_cannot_access_unassigned_patient_detail(self):
        """Лікар не може переглянути детальну інформацію непризначеного пацієнта"""
        self.client.login(username='doctor_test', password='doctor123')
        url = reverse('patients:patient_detail', kwargs={'patient_id': self.other_patient_profile.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 302)  # Редирект
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('немає доступу' in str(m) for m in messages))
    
    def test_admin_can_access_all_patients(self):
        """Адміністратори мають доступ до всіх пацієнтів"""
        self.client.login(username='admin_test', password='admin123')
        response = self.client.get(reverse('patients:patient_list'))
        
        self.assertEqual(response.status_code, 200)
        patients = response.context['patients']
        patient_ids = [p.id for p in patients]
        
        self.assertIn(self.patient_profile.id, patient_ids)
        self.assertIn(self.other_patient_profile.id, patient_ids)


class DataLeakageTests(SecurityTestCase):
    """Тести на витік даних"""
    
    def test_patient_data_not_in_response_for_unauthorized(self):
        """Дані пацієнтів не повертаються неавторизованим користувачам"""
        # Спроба доступу без авторизації
        url = reverse('patients:patient_detail', kwargs={'patient_id': self.patient_profile.id})
        response = self.client.get(url)
        
        # Не повинно бути даних пацієнта в відповіді
        response_content = response.content.decode()
        self.assertNotIn(self.patient_user.email, response_content)
        self.assertNotIn(self.patient_profile.emergency_contact_phone, response_content)
    
    def test_no_sensitive_data_in_error_messages(self):
        """Чутливі дані не потрапляють в повідомлення про помилки"""
        self.client.login(username='doctor_test', password='doctor123')
        
        # Спроба доступу до неіснуючого пацієнта
        url = reverse('patients:patient_detail', kwargs={'patient_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
        # Перевіряємо, що в помилці немає чутливої інформації
        response_content = response.content.decode()
        self.assertNotIn('database', response_content.lower())
        self.assertNotIn('sql', response_content.lower())


class AuthenticationSecurityTests(SecurityTestCase):
    """Тести безпеки автентифікації"""
    
    def test_login_attempts_tracking(self):
        """Тестування відстеження невдалих спроб входу"""
        login_url = reverse('core:login')
        
        # 5 невдалих спроб
        for i in range(5):
            response = self.client.post(login_url, {
                'username': 'patient_test',
                'password': 'wrong_password'
            })
            self.assertEqual(response.status_code, 200)
        
        # Перевіряємо, що аккаунт заблокований
        user = User.objects.get(username='patient_test')
        self.assertEqual(user.failed_login_attempts, 5)
        self.assertIsNotNone(user.account_locked_until)
        
        # Спроба входу з правильним паролем повинна не вдатися
        response = self.client.post(login_url, {
            'username': 'patient_test',
            'password': 'patient123'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('заблокований' in str(m) for m in messages))
    
    def test_successful_login_resets_failed_attempts(self):
        """Успішний вхід скидає лічильник невдалих спроб"""
        user = User.objects.get(username='patient_test')
        user.failed_login_attempts = 3
        user.save()
        
        login_url = reverse('core:login')
        response = self.client.post(login_url, {
            'username': 'patient_test',
            'password': 'patient123'
        })
        
        # Перевіряємо редирект (успішний вхід)
        self.assertEqual(response.status_code, 302)
        
        # Перевіряємо, що лічильник скинутий
        user.refresh_from_db()
        self.assertEqual(user.failed_login_attempts, 0)
        self.assertIsNone(user.account_locked_until)


class InputValidationTests(SecurityTestCase):
    """Тести валідації вводу"""
    
    def test_patient_form_validates_phone_number(self):
        """Форма пацієнта валідує номер телефону"""
        from patients.forms import PatientProfileForm
        
        # Невалідний номер телефону
        form_data = {
            'gender': 'M',
            'emergency_contact_name': 'Test Contact',
            'emergency_contact_phone': 'invalid-phone',
        }
        form = PatientProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('emergency_contact_phone', form.errors)
        
        # Валідний номер телефону
        form_data['emergency_contact_phone'] = '+380501234567'
        form = PatientProfileForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_xss_protection_in_forms(self):
        """Тестування захисту від XSS у формах"""
        self.client.login(username='doctor_test', password='doctor123')
        
        # Спроба введення XSS коду
        xss_payload = '<script>alert("XSS")</script>'
        
        url = reverse('patients:add_rehabilitation_record', 
                     kwargs={'patient_id': self.patient_profile.id})
        
        response = self.client.post(url, {
            'injury_type': xss_payload,
            'injury_date': '2024-01-01',
            'diagnosis': 'Test diagnosis',
            'notes': 'Test notes'
        })
        
        # Перевіряємо, що XSS код не виконується
        if response.status_code == 302:  # Успішне збереження
            # Перевіряємо, що в базі даних XSS код зберігається як текст
            from patients.models import RehabilitationHistory
            record = RehabilitationHistory.objects.filter(
                patient=self.patient_profile,
                injury_type__contains='script'
            ).first()
            
            if record:
                # Отримуємо сторінку деталей
                detail_url = reverse('patients:rehabilitation_record_detail',
                                   kwargs={
                                       'patient_id': self.patient_profile.id,
                                       'record_id': record.id
                                   })
                detail_response = self.client.get(detail_url)
                detail_content = detail_response.content.decode()
                
                # XSS код повинен бути екранований
                self.assertNotIn('<script>', detail_content)
                self.assertIn('&lt;script&gt;', detail_content)


class PermissionTests(SecurityTestCase):
    """Тести дозволів Django"""
    
    def test_user_permissions_assignment(self):
        """Тестування призначення дозволів користувачам"""
        # Перевіряємо, що у користувачів є правильні дозволи
        self.assertTrue(self.admin_user.has_perm('auth.add_user'))
        self.assertFalse(self.patient_user.has_perm('auth.add_user'))
        self.assertFalse(self.doctor_user.has_perm('auth.add_user'))
    
    def test_role_based_access_to_admin_functions(self):
        """Тільки адміністратори мають доступ до адміністративних функцій"""
        # Спроба призначення лікаря (тільки для адмінів)
        assign_url = reverse('patients:assign_doctor', 
                           kwargs={'patient_id': self.patient_profile.id})
        
        # Лікар не може призначати інших лікарів
        self.client.login(username='doctor_test', password='doctor123')
        response = self.client.post(assign_url, {
            'doctor_id': self.doctor_profile.id
        })
        self.assertEqual(response.status_code, 403)
        
        # Адміністратор може
        self.client.login(username='admin_test', password='admin123')
        response = self.client.post(assign_url, {
            'doctor_id': self.doctor_profile.id
        })
        # Лікар уже призначений, тому очікуємо помилку
        self.assertEqual(response.status_code, 400)


class SessionSecurityTests(SecurityTestCase):
    """Тести безпеки сесій"""
    
    def test_session_expires_after_logout(self):
        """Сесія закінчується після виходу"""
        # Вхід
        self.client.login(username='patient_test', password='patient123')
        
        # Перевіряємо доступ до захищеної сторінки
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 302)  # Редирект на роль-специфічний дашборд
        
        # Вихід
        self.client.get(reverse('core:logout'))
        
        # Спроба доступу після виходу
        response = self.client.get(reverse('core:dashboard'))
        self.assertRedirects(response, '/auth/login/?next=/dashboard/')
    
    def test_concurrent_sessions_handling(self):
        """Тестування обробки одночасних сесій"""
        client1 = Client()
        client2 = Client()
        
        # Два входи з одним аккаунтом
        client1.login(username='patient_test', password='patient123')
        client2.login(username='patient_test', password='patient123')
        
        # Обидва клієнти повинні мати доступ
        response1 = client1.get(reverse('core:dashboard'))
        response2 = client2.get(reverse('core:dashboard'))
        
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response2.status_code, 302)


# Функція для запуску всіх тестів безпеки
def run_security_tests():
    """Запуск всіх тестів безпеки"""
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Додаємо всі тестові класи
    test_classes = [
        AccessControlTests,
        DataLeakageTests,
        AuthenticationSecurityTests,
        InputValidationTests,
        PermissionTests,
        SessionSecurityTests,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)