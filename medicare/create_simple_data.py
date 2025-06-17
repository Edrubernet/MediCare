#!/usr/bin/env python
"""
Простий скрипт для створення базових даних без складних залежностей
"""
import os
import sys
import django

sys.path.append('/mnt/c/Users/lustu/Робочий стіл/medicare_v1.2/medicare')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicare.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import datetime, timedelta
import random

User = get_user_model()

# Створюємо адміністратора
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@medicare.com',
        'first_name': 'Олександр',
        'last_name': 'Адміністраторенко',
        'user_type': 'admin',
        'is_staff': True,
        'is_superuser': True,
        'password': make_password('admin123'),
    }
)
print(f"Адміністратор: {'створено' if created else 'вже існує'}")

# Створюємо лікарів
from staff.models import StaffProfile

doctors_data = [
    {
        'username': 'dr_petrov',
        'email': 'petrov@medicare.com',
        'first_name': 'Петро',
        'last_name': 'Петренко',
        'specialization': 'Фізіотерапевт',
        'bio': 'Спеціаліст з реабілітації після травм. Понад 15 років досвіду.'
    },
    {
        'username': 'dr_ivanova',
        'email': 'ivanova@medicare.com',
        'first_name': 'Марія',
        'last_name': 'Іваненко',
        'specialization': 'Невролог-реабілітолог',
        'bio': 'Експерт з неврологічної реабілітації та відновлення після інсульту.'
    }
]

doctors = []
for doctor_data in doctors_data:
    user, created = User.objects.get_or_create(
        username=doctor_data['username'],
        defaults={
            'email': doctor_data['email'],
            'first_name': doctor_data['first_name'],
            'last_name': doctor_data['last_name'],
            'user_type': 'doctor',
            'is_staff': True,
            'password': make_password('doctor123'),
        }
    )
    print(f"Лікар {user.get_full_name()}: {'створено' if created else 'вже існує'}")
    
    if created or not hasattr(user, 'staff_profile'):
        staff_profile, profile_created = StaffProfile.objects.get_or_create(
            user=user,
            defaults={
                'specialization': doctor_data['specialization'],
                'bio': doctor_data['bio']
            }
        )
        print(f"  Профіль: {'створено' if profile_created else 'вже існує'}")
    
    doctors.append(user)

# Створюємо пацієнтів
from patients.models import PatientProfile

patients_data = [
    {
        'username': 'patient_shevchenko',
        'email': 'shevchenko@example.com',
        'first_name': 'Тарас',
        'last_name': 'Шевченко',
        'phone_number': '+380501234567',
        'date_of_birth': '1985-03-15',
        'gender': 'M',
        'address': 'м. Київ, вул. Хрещатик, 25',
        'emergency_contact_name': 'Марія Шевченко',
        'emergency_contact_phone': '+380509876543'
    },
    {
        'username': 'patient_kovalchuk',
        'email': 'kovalchuk@example.com',
        'first_name': 'Оксана',
        'last_name': 'Ковальчук',
        'phone_number': '+380502345678',
        'date_of_birth': '1975-07-22',
        'gender': 'F',
        'address': 'м. Львів, вул. Городоцька, 158',
        'emergency_contact_name': 'Петро Ковальчук',
        'emergency_contact_phone': '+380508765432'
    }
]

patients = []
for patient_data in patients_data:
    user, created = User.objects.get_or_create(
        username=patient_data['username'],
        defaults={
            'email': patient_data['email'],
            'first_name': patient_data['first_name'],
            'last_name': patient_data['last_name'],
            'user_type': 'patient',
            'phone_number': patient_data['phone_number'],
            'password': make_password('patient123'),
        }
    )
    print(f"Пацієнт {user.get_full_name()}: {'створено' if created else 'вже існує'}")
    
    if created or not hasattr(user, 'patient_profile'):
        patient_profile, profile_created = PatientProfile.objects.get_or_create(
            user=user,
            defaults={
                'date_of_birth': datetime.strptime(patient_data['date_of_birth'], '%Y-%m-%d').date(),
                'gender': patient_data['gender'],
                'address': patient_data['address'],
                'emergency_contact_name': patient_data['emergency_contact_name'],
                'emergency_contact_phone': patient_data['emergency_contact_phone']
            }
        )
        print(f"  Профіль: {'створено' if profile_created else 'вже існує'}")
    
    patients.append(user)

# Створюємо базові сповіщення
from notification.models import Notification

notification_count = 0
for user in doctors + patients:
    for _ in range(random.randint(2, 5)):
        notification, created = Notification.objects.get_or_create(
            recipient=user,
            title=f'Тестове сповіщення для {user.get_full_name()}',
            defaults={
                'notification_type': random.choice(['appointment', 'reminder', 'system']),
                'message': f'Це тестове повідомлення для перевірки системи сповіщень.',
                'is_read': random.choice([True, False]),
                'created_at': timezone.now() - timedelta(days=random.randint(1, 10))
            }
        )
        if created:
            notification_count += 1

print(f"Створено {notification_count} сповіщень")

print("\n" + "="*50)
print("БАЗОВІ ДАНІ СТВОРЕНО!")
print("="*50)
print("Дані для входу:")
print("Адміністратор: admin / admin123")
print("Лікар: dr_petrov / doctor123")
print("Пацієнт: patient_shevchenko / patient123")
print("="*50)