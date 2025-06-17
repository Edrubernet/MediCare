#!/usr/bin/env python3
"""
Скрипт для діагностики та створення тестових даних для панелі терапевта
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
from patients.models import PatientProfile, MedicalHistory
from consultation.models import Consultation
from programs.models import RehabilitationProgram

def check_database_state():
    """Перевірка стану бази даних"""
    print("=" * 60)
    print("🔍 ДІАГНОСТИКА БАЗИ ДАНИХ")
    print("=" * 60)
    
    # Перевіряємо користувачів
    total_users = User.objects.count()
    doctors = User.objects.filter(user_type='doctor').count()
    patients = User.objects.filter(user_type='patient').count()
    
    print(f"👥 Користувачі:")
    print(f"   Всього: {total_users}")
    print(f"   Лікарі: {doctors}")
    print(f"   Пацієнти: {patients}")
    
    # Перевіряємо профілі
    staff_profiles = StaffProfile.objects.count()
    patient_profiles = PatientProfile.objects.count()
    
    print(f"\n📋 Профілі:")
    print(f"   Профілі персоналу: {staff_profiles}")
    print(f"   Профілі пацієнтів: {patient_profiles}")
    
    # Перевіряємо консультації
    consultations = Consultation.objects.count()
    today_consultations = Consultation.objects.filter(
        start_time__date=timezone.now().date()
    ).count()
    
    print(f"\n🩺 Консультації:")
    print(f"   Всього: {consultations}")
    print(f"   На сьогодні: {today_consultations}")
    
    # Перевіряємо програми
    programs = RehabilitationProgram.objects.count()
    active_programs = RehabilitationProgram.objects.filter(status='active').count()
    
    print(f"\n🏥 Програми реабілітації:")
    print(f"   Всього: {programs}")
    print(f"   Активних: {active_programs}")
    
    # Перевіряємо зв'язки
    print(f"\n🔗 Зв'язки:")
    for profile in StaffProfile.objects.all()[:3]:
        assigned_patients = profile.patients.count()
        print(f"   Лікар {profile.user.get_full_name()}: {assigned_patients} пацієнтів")

def create_test_data():
    """Створення тестових даних"""
    print("\n" + "=" * 60)
    print("🔧 СТВОРЕННЯ ТЕСТОВИХ ДАНИХ")
    print("=" * 60)
    
    # Створюємо лікаря, якщо немає
    doctor_user, created = User.objects.get_or_create(
        username='test_doctor',
        defaults={
            'email': 'doctor@test.com',
            'first_name': 'Олександр',
            'last_name': 'Петренко',
            'user_type': 'doctor',
            'phone_number': '+380501234567'
        }
    )
    if created:
        doctor_user.set_password('doctor123')
        doctor_user.save()
        print(f"✅ Створено лікаря: {doctor_user.username}")
    
    # Створюємо профіль лікаря
    doctor_profile, created = StaffProfile.objects.get_or_create(
        user=doctor_user,
        defaults={
            'specialization': 'Фізична реабілітація',
            'bio': 'Тестовий лікар для демонстрації системи'
        }
    )
    if created:
        print(f"✅ Створено профіль лікаря")
    
    # Створюємо пацієнта
    patient_user, created = User.objects.get_or_create(
        username='test_patient',
        defaults={
            'email': 'patient@test.com',
            'first_name': 'Марія',
            'last_name': 'Іваненко',
            'user_type': 'patient',
            'phone_number': '+380501234568'
        }
    )
    if created:
        patient_user.set_password('patient123')
        patient_user.save()
        print(f"✅ Створено пацієнта: {patient_user.username}")
    
    # Створюємо профіль пацієнта
    patient_profile, created = PatientProfile.objects.get_or_create(
        user=patient_user,
        defaults={
            'date_of_birth': date(1985, 3, 15),
            'gender': 'F',
            'address': 'м. Київ, вул. Тестова 1',
            'emergency_contact_name': 'Іван Іваненко',
            'emergency_contact_phone': '+380501234569'
        }
    )
    if created:
        print(f"✅ Створено профіль пацієнта")
    
    # Призначаємо пацієнта лікарю
    patient_profile.assigned_doctors.add(doctor_profile)
    print(f"✅ Пацієнта призначено лікарю")
    
    # Створюємо консультацію на сьогодні
    today = timezone.now().date()
    start_time = timezone.make_aware(datetime.combine(today, datetime.now().time().replace(hour=14, minute=0)))
    end_time = start_time + timedelta(hours=1)
    
    consultation, created = Consultation.objects.get_or_create(
        doctor=doctor_profile,
        patient=patient_profile,
        start_time=start_time,
        defaults={
            'end_time': end_time,
            'consultation_type': 'in_person',
            'status': 'scheduled',
            'notes': 'Тестова консультація'
        }
    )
    if created:
        print(f"✅ Створено консультацію на сьогодні: {start_time}")
    
    # Створюємо програму реабілітації
    program, created = RehabilitationProgram.objects.get_or_create(
        patient=patient_profile,
        doctor=doctor_profile,
        title='Тестова програма реабілітації',
        defaults={
            'description': 'Програма для тестування панелі лікаря',
            'start_date': today,
            'end_date': today + timedelta(days=30),
            'status': 'active'
        }
    )
    if created:
        print(f"✅ Створено програму реабілітації: {program.title}")

def main():
    """Головна функція"""
    print("🚀 ДІАГНОСТИКА ПАНЕЛІ ТЕРАПЕВТА")
    
    # Спочатку перевіряємо стан
    check_database_state()
    
    # Якщо даних мало, створюємо тестові
    if (User.objects.filter(user_type='doctor').count() == 0 or 
        PatientProfile.objects.count() == 0 or
        Consultation.objects.count() == 0):
        
        print("\n⚠️  Виявлено мало даних. Створюємо тестові дані...")
        create_test_data()
        
        print("\n🔄 Повторна перевірка після створення даних:")
        check_database_state()
    
    print("\n" + "=" * 60)
    print("✅ ДІАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 60)
    print("\n💡 Тепер спробуйте оновити панель терапевта")
    print("   URL: /therapist-dashboard/")
    print(f"   Логін лікаря: test_doctor / doctor123")

if __name__ == '__main__':
    main()