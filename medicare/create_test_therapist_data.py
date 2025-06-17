#!/usr/bin/env python3
"""
Простий скрипт для створення тестових даних для панелі терапевта
"""
import os
import sys
import django
from datetime import date, datetime, timedelta

# Налаштовуємо Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicare.settings')
django.setup()

from django.utils import timezone
from staff.models import User, StaffProfile
from patients.models import PatientProfile
from consultation.models import Consultation
from programs.models import RehabilitationProgram

# Перевіряємо що є в базі
print("=== ПЕРЕВІРКА БАЗИ ДАНИХ ===")
print(f"Всього користувачів: {User.objects.count()}")
print(f"Лікарів: {User.objects.filter(user_type='doctor').count()}")
print(f"Пацієнтів: {User.objects.filter(user_type='patient').count()}")
print(f"Консультацій: {Consultation.objects.count()}")
print(f"Програм: {RehabilitationProgram.objects.count()}")

# Знаходимо першого лікаря
doctor_users = User.objects.filter(user_type='doctor')
if doctor_users.exists():
    doctor_user = doctor_users.first()
    print(f"\nЗнайдено лікаря: {doctor_user.get_full_name()} ({doctor_user.username})")
    
    try:
        doctor_profile = doctor_user.staff_profile
        print(f"Профіль лікаря знайдено: ID {doctor_profile.id}")
        
        # Перевіряємо пацієнтів цього лікаря
        patients = doctor_profile.patients.all()
        print(f"Пацієнтів призначено: {patients.count()}")
        
        # Перевіряємо консультації
        consultations = Consultation.objects.filter(doctor=doctor_profile)
        print(f"Консультацій лікаря: {consultations.count()}")
        
        # Перевіряємо сьогоднішні консультації
        today = timezone.now().date()
        today_consultations = consultations.filter(start_time__date=today)
        print(f"Консультацій на сьогодні ({today}): {today_consultations.count()}")
        
        # Показуємо всі консультації з датами
        for consultation in consultations:
            print(f"  Консультація: {consultation.patient.user.get_full_name()} - {consultation.start_time}")
            
    except Exception as e:
        print(f"Помилка з профілем лікаря: {e}")
else:
    print("Лікарів не знайдено!")

print("\n=== ЗАВЕРШЕНО ===")