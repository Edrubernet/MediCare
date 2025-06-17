#!/usr/bin/env python
"""
Скрипт для заповнення бази даних тестовими даними
"""
import os
import sys
import django
from datetime import datetime, timedelta, time
from django.utils import timezone
import random

# Додаємо шлях до проекту
sys.path.append('/mnt/c/Users/lustu/Робочий стіл/medicare_v1.2/medicare')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicare.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from patients.models import PatientProfile
from staff.models import StaffProfile
from consultation.models import Consultation
from programs.models import RehabilitationProgram, Appointment, ProgressLog, ProgramDay, ProgramExercise
from exercises.models import Exercise, ExerciseCategory
from notification.models import Notification
from progress.models import Session, Note, Photo

User = get_user_model()

def create_users():
    """Створення користувачів"""
    print("Створюю користувачів...")
    
    # Адміністратор
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
            'date_joined': timezone.now() - timedelta(days=30)
        }
    )
    
    # Лікарі
    doctors_data = [
        {
            'username': 'dr_petrov',
            'email': 'petrov@medicare.com',
            'first_name': 'Петро',
            'last_name': 'Петренко',
            'specialization': 'Фізіотерапевт',
            'qualification': 'Кандидат медичних наук',
            'experience_years': 15,
            'bio': 'Спеціаліст з реабілітації після травм опорно-рухового апарату. Понад 15 років досвіду.'
        },
        {
            'username': 'dr_ivanova',
            'email': 'ivanova@medicare.com',
            'first_name': 'Марія',
            'last_name': 'Іваненко',
            'specialization': 'Невролог-реабілітолог',
            'qualification': 'Лікар вищої категорії',
            'experience_years': 12,
            'bio': 'Експерт з неврологічної реабілітації та відновлення після інсульту.'
        },
        {
            'username': 'dr_kovalenko',
            'email': 'kovalenko@medicare.com',
            'first_name': 'Андрій',
            'last_name': 'Коваленко',
            'specialization': 'Ортопед-травматолог',
            'qualification': 'Доктор медичних наук',
            'experience_years': 20,
            'bio': 'Провідний спеціаліст з хірургії та реабілітації травм кістково-м\'язової системи.'
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
                'date_joined': timezone.now() - timedelta(days=random.randint(20, 40))
            }
        )
        
        if created or not hasattr(user, 'staff_profile'):
            staff_profile, _ = StaffProfile.objects.get_or_create(
                user=user,
                defaults={
                    'specialization': doctor_data['specialization'],
                    'qualification': doctor_data['qualification'],
                    'experience_years': doctor_data['experience_years'],
                    'bio': doctor_data['bio'],
                    'is_active': True
                }
            )
        doctors.append(user)
    
    # Пацієнти
    patients_data = [
        {
            'username': 'patient_shevchenko',
            'email': 'shevchenko@example.com',
            'first_name': 'Тарас',
            'last_name': 'Шевченко',
            'birth_date': '1985-03-15',
            'phone': '+380501234567',
            'emergency_contact': 'Дружина: +380509876543',
            'medical_history': 'Травма коліна після ДТП у 2023 році. Проходив операцію з відновлення зв\'язок.',
            'current_condition': 'Відновлення після операції на коліні, обмежена рухливість.'
        },
        {
            'username': 'patient_kovalchuk',
            'email': 'kovalchuk@example.com',
            'first_name': 'Оксана',
            'last_name': 'Ковальчук',
            'birth_date': '1975-07-22',
            'phone': '+380502345678',
            'emergency_contact': 'Син: +380508765432',
            'medical_history': 'Інсульт у 2023 році. Порушення мовлення та рухових функцій.',
            'current_condition': 'Відновлення після інсульту, проходить мовну та фізичну терапію.'
        },
        {
            'username': 'patient_bondarenko',
            'email': 'bondarenko@example.com',
            'first_name': 'Василь',
            'last_name': 'Бондаренко',
            'birth_date': '1990-11-08',
            'phone': '+380503456789',
            'emergency_contact': 'Мати: +380507654321',
            'medical_history': 'Хронічний біль у спині через сидячу роботу. Сколіоз.',
            'current_condition': 'Хронічний біль у поперековому відділі хребта.'
        },
        {
            'username': 'patient_lysenko',
            'email': 'lysenko@example.com',
            'first_name': 'Ірина',
            'last_name': 'Лисенко',
            'birth_date': '1988-12-03',
            'phone': '+380504567890',
            'emergency_contact': 'Чоловік: +380506543210',
            'medical_history': 'Перелом правої руки у 2024 році.',
            'current_condition': 'Відновлення після перелому, проходить фізіотерапію.'
        },
        {
            'username': 'patient_moroz',
            'email': 'moroz@example.com',
            'first_name': 'Віктор',
            'last_name': 'Мороз',
            'birth_date': '1980-04-17',
            'phone': '+380505678901',
            'emergency_contact': 'Сестра: +380505432109',
            'medical_history': 'Артрит колінних суглобів.',
            'current_condition': 'Хронічні болі в колінах, зниження рухливості.'
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
                'password': make_password('patient123'),
                'date_joined': timezone.now() - timedelta(days=random.randint(10, 50))
            }
        )
        
        if created or not hasattr(user, 'patient_profile'):
            patient_profile, _ = PatientProfile.objects.get_or_create(
                user=user,
                defaults={
                    'birth_date': datetime.strptime(patient_data['birth_date'], '%Y-%m-%d').date(),
                    'phone': patient_data['phone'],
                    'emergency_contact': patient_data['emergency_contact'],
                    'medical_history': patient_data['medical_history'],
                    'current_condition': patient_data['current_condition']
                }
            )
        patients.append(user)
    
    print(f"Створено: 1 адміністратор, {len(doctors)} лікарів, {len(patients)} пацієнтів")
    return admin, doctors, patients

def create_exercise_categories_and_exercises():
    """Створення категорій вправ та вправ"""
    print("Створюю вправи...")
    
    categories_data = [
        {
            'name': 'Розтяжка',
            'description': 'Вправи для покращення гнучкості та розтяжки м\'язів'
        },
        {
            'name': 'Силові вправи',
            'description': 'Вправи для зміцнення м\'язів'
        },
        {
            'name': 'Кардіо',
            'description': 'Вправи для покращення серцево-судинної системи'
        },
        {
            'name': 'Баланс',
            'description': 'Вправи для покращення координації та рівноваги'
        },
        {
            'name': 'Дихальні вправи',
            'description': 'Вправи для покращення дихання та релаксації'
        }
    ]
    
    categories = []
    for cat_data in categories_data:
        category, _ = ExerciseCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        categories.append(category)
    
    exercises_data = [
        # Розтяжка
        {
            'title': 'Розтяжка шийних м\'язів',
            'description': 'М\'яка розтяжка м\'язів шиї для зняття напруження',
            'instructions': '1. Сідьте прямо\n2. Повільно нахиліть голову вправо\n3. Тримайте 15 секунд\n4. Повторіть в інший бік',
            'category': categories[0],
            'difficulty': 'beginner',
            'duration': 5
        },
        {
            'title': 'Розтяжка спини',
            'description': 'Розтяжка м\'язів спини для зменшення болю',
            'instructions': '1. Лягте на спину\n2. Підтягніть коліна до грудей\n3. Тримайте 20 секунд\n4. Повторіть 3 рази',
            'category': categories[0],
            'difficulty': 'beginner',
            'duration': 10
        },
        # Силові вправи
        {
            'title': 'Планка',
            'description': 'Базова вправа для зміцнення м\'язів корсету',
            'instructions': '1. Станьте у положення планки\n2. Тримайте тіло прямо\n3. Утримуйте позицію 30 секунд\n4. Відпочиньте та повторіть',
            'category': categories[1],
            'difficulty': 'intermediate',
            'duration': 15
        },
        {
            'title': 'Присідання',
            'description': 'Зміцнення м\'язів ніг та сідниць',
            'instructions': '1. Поставте ноги на ширині плечей\n2. Повільно присядьте\n3. Встаньте у вихідне положення\n4. Повторіть 10-15 разів',
            'category': categories[1],
            'difficulty': 'beginner',
            'duration': 10
        },
        # Кардіо
        {
            'title': 'Ходьба на місці',
            'description': 'М\'яке кардіо навантаження',
            'instructions': '1. Станьте прямо\n2. Піднімайте коліна по черзі\n3. Рухайте руками\n4. Продовжуйте 5-10 хвилин',
            'category': categories[2],
            'difficulty': 'beginner',
            'duration': 10
        },
        # Баланс
        {
            'title': 'Стояння на одній нозі',
            'description': 'Покращення рівноваги та координації',
            'instructions': '1. Станьте на одну ногу\n2. Тримайте рівновагу 30 секунд\n3. Поміняйте ногу\n4. Повторіть 3 рази',
            'category': categories[3],
            'difficulty': 'intermediate',
            'duration': 5
        },
        # Дихальні вправи
        {
            'title': 'Глибоке дихання',
            'description': 'Техніка релаксації та покращення дихання',
            'instructions': '1. Сядьте зручно\n2. Вдихніть повільно через ніс 4 секунди\n3. Затримайте дихання на 4 секунди\n4. Видихніть через рот 6 секунд',
            'category': categories[4],
            'difficulty': 'beginner',
            'duration': 8
        }
    ]
    
    exercises = []
    for ex_data in exercises_data:
        exercise, _ = Exercise.objects.get_or_create(
            title=ex_data['title'],
            defaults={
                'description': ex_data['description'],
                'instructions': ex_data['instructions'],
                'category': ex_data['category'],
                'difficulty_level': ex_data['difficulty'],
                'estimated_duration': ex_data['duration'],
                'created_at': timezone.now() - timedelta(days=random.randint(5, 30))
            }
        )
        exercises.append(exercise)
    
    print(f"Створено: {len(categories)} категорій, {len(exercises)} вправ")
    return exercises

def create_programs_and_appointments(doctors, patients, exercises):
    """Створення програм реабілітації та прийомів"""
    print("Створюю програми реабілітації...")
    
    programs = []
    appointments = []
    
    # Для кожного пацієнта створюємо програму
    for i, patient in enumerate(patients):
        doctor = doctors[i % len(doctors)]
        
        # Дати: деякі програми почалися тижні тому
        start_date = timezone.now().date() - timedelta(days=random.randint(14, 35))
        end_date = start_date + timedelta(days=random.randint(30, 90))
        
        program_titles = [
            f"Відновлення після травми коліна - {patient.get_full_name()}",
            f"Реабілітація після інсульту - {patient.get_full_name()}",
            f"Лікування болю в спині - {patient.get_full_name()}",
            f"Відновлення після перелому - {patient.get_full_name()}",
            f"Терапія артриту - {patient.get_full_name()}"
        ]
        
        program_descriptions = [
            "Комплексна програма відновлення функцій коліна після травми",
            "Мультидисциплінарна програма реабілітації після інсульту",
            "Програма зменшення болю та покращення рухливості спини",
            "Поетапне відновлення після перелому кістки",
            "Програма управління болем при артриті"
        ]
        
        program = RehabilitationProgram.objects.create(
            title=program_titles[i],
            description=program_descriptions[i],
            patient=patient.patient_profile,
            doctor=doctor.staff_profile,
            start_date=start_date,
            end_date=end_date,
            status=random.choice(['active', 'active', 'active', 'completed']),
            goals=f"Покращити рухливість, зменшити біль, відновити функціональність",
            expected_outcomes="Повне або часткове відновлення функцій",
            sessions_per_week=random.randint(2, 4),
            session_duration=random.randint(45, 90)
        )
        programs.append(program)
        
        # Створюємо дні програми з вправами
        for day in range(1, random.randint(5, 10)):
            program_day = ProgramDay.objects.create(
                program=program,
                day_number=day,
                notes=f"День {day}: фокус на {random.choice(['розтяжку', 'силові вправи', 'координацію'])}"
            )
            
            # Додаємо вправи до дня
            day_exercises = random.sample(exercises, random.randint(2, 4))
            for order, exercise in enumerate(day_exercises):
                ProgramExercise.objects.create(
                    program_day=program_day,
                    exercise=exercise,
                    sets=random.randint(1, 3),
                    repetitions=random.randint(5, 15),
                    duration=random.randint(30, 180),
                    rest_between_sets=random.randint(30, 90),
                    order=order,
                    additional_instructions=f"Виконувати {random.choice(['повільно', 'з контролем', 'без болю'])}"
                )
        
        # Створюємо прийоми для програми
        appointment_date = start_date
        while appointment_date <= min(end_date, timezone.now().date() + timedelta(days=7)):
            if appointment_date.weekday() < 5:  # Тільки робочі дні
                appointment = Appointment.objects.create(
                    patient=patient.patient_profile,
                    doctor=doctor.staff_profile,
                    appointment_type=random.choice(['therapy_session', 'assessment', 'follow_up']),
                    date=appointment_date,
                    start_time=time(random.randint(9, 16), random.choice([0, 30])),
                    end_time=time(random.randint(10, 17), random.choice([0, 30])),
                    status='completed' if appointment_date < timezone.now().date() else random.choice(['scheduled', 'confirmed']),
                    description=f"Сеанс реабілітації в рамках програми {program.title}",
                    related_program=program,
                    notes=f"Пацієнт показав {random.choice(['хороший', 'задовільний', 'відмінний'])} прогрес"
                )
                appointments.append(appointment)
            
            appointment_date += timedelta(days=random.randint(2, 7))
    
    print(f"Створено: {len(programs)} програм, {len(appointments)} прийомів")
    return programs, appointments

def create_consultations(doctors, patients):
    """Створення консультацій"""
    print("Створюю консультації...")
    
    consultations = []
    
    for patient in patients:
        doctor = random.choice(doctors)
        
        # Створюємо 2-4 консультації для кожного пацієнта
        for _ in range(random.randint(2, 4)):
            start_time = timezone.now() - timedelta(
                days=random.randint(1, 30),
                hours=random.randint(8, 17),
                minutes=random.choice([0, 30])
            )
            end_time = start_time + timedelta(minutes=random.randint(30, 90))
            
            consultation = Consultation.objects.create(
                patient=patient.patient_profile,
                doctor=doctor.staff_profile,
                start_time=start_time,
                end_time=end_time,
                consultation_type=random.choice(['in_person', 'video']),
                status=random.choice(['completed', 'completed', 'scheduled', 'canceled']),
                reason=random.choice([
                    'Первинна консультація',
                    'Контрольний огляд',
                    'Оцінка прогресу',
                    'Коригування лікування',
                    'Скарги на біль'
                ]),
                diagnosis=random.choice([
                    'Травма коліна',
                    'Хронічний біль у спині',
                    'Відновлення після інсульту',
                    'Артрит',
                    'Перелом кістки'
                ]),
                treatment_plan=f"Призначено {random.choice(['фізіотерапію', 'медикаментозне лікування', 'лікувальну гімнастику'])}",
                notes=f"Пацієнт скаржиться на {random.choice(['біль', 'обмежену рухливість', 'слабкість'])}. Призначено подальше лікування."
            )
            consultations.append(consultation)
    
    print(f"Створено: {len(consultations)} консультацій")
    return consultations

def create_progress_data(patients, doctors, programs):
    """Створення даних прогресу"""
    print("Створюю дані прогресу...")
    
    sessions = []
    notes = []
    photos = []
    progress_logs = []
    
    for patient in patients:
        doctor = random.choice(doctors)
        
        # Створюємо сеанси
        for _ in range(random.randint(5, 15)):
            session_date = timezone.now() - timedelta(days=random.randint(1, 30))
            
            session = Session.objects.create(
                patient=patient.patient_profile,
                therapist=doctor.staff_profile,
                date=session_date.date(),
                start_time=session_date.time(),
                end_time=(session_date + timedelta(hours=1)).time(),
                session_type=random.choice(['physiotherapy', 'occupational_therapy', 'speech_therapy', 'psychological']),
                status='completed',
                notes=f"Пацієнт виконав {random.choice(['всі', 'більшість', 'частину'])} вправ. Прогрес {random.choice(['хороший', 'задовільний', 'відмінний'])}.",
                goals_achieved=random.choice([True, True, False]),
                pain_level_before=random.randint(3, 8),
                pain_level_after=random.randint(1, 5),
                patient_feedback=random.choice([
                    'Почуваюся краще',
                    'Менше болить',
                    'Складно виконувати вправи',
                    'Хороший прогрес',
                    'Потрібно більше часу'
                ])
            )
            sessions.append(session)
        
        # Створюємо нотатки
        for _ in range(random.randint(3, 8)):
            note_date = timezone.now() - timedelta(days=random.randint(1, 25))
            
            note = Note.objects.create(
                patient=patient.patient_profile,
                author=doctor.staff_profile,
                title=random.choice([
                    'Оцінка прогресу',
                    'Зміна в лікуванні',
                    'Нові скарги',
                    'Покращення стану',
                    'Рекомендації'
                ]),
                content=random.choice([
                    'Пацієнт показує стабільний прогрес у відновленні рухливості.',
                    'Відмічається зменшення больового синдрому.',
                    'Рекомендовано збільшити інтенсивність вправ.',
                    'Пацієнт скаржиться на втому після тренувань.',
                    'Потрібно скоригувати програму реабілітації.'
                ]),
                note_type=random.choice(['assessment', 'treatment', 'progress', 'concern']),
                created_at=note_date
            )
            notes.append(note)
        
        # Створюємо фото прогресу
        for _ in range(random.randint(1, 4)):
            photo_date = timezone.now() - timedelta(days=random.randint(1, 20))
            
            photo = Photo.objects.create(
                patient=patient.patient_profile,
                title=random.choice([
                    'Фото стану до лікування',
                    'Прогрес через тиждень',
                    'Рентген після операції',
                    'Стан через місяць лікування'
                ]),
                description=f"Документація прогресу пацієнта {patient.get_full_name()}",
                photo_type=random.choice(['before', 'progress', 'after', 'xray']),
                taken_date=photo_date.date(),
                # Не вказуємо image_file, оскільки файли відсутні
                notes=f"Фото зроблено для відстеження прогресу лікування"
            )
            photos.append(photo)
        
        # Створюємо логи прогресу
        patient_program = programs[patients.index(patient)] if patients.index(patient) < len(programs) else None
        
        for _ in range(random.randint(3, 10)):
            log_date = timezone.now() - timedelta(days=random.randint(1, 25))
            
            progress_log = ProgressLog.objects.create(
                patient=patient.patient_profile,
                doctor=doctor.staff_profile,
                progress_type=random.choice(['exercise', 'pain_level', 'mobility', 'general']),
                log_date=log_date,
                notes=random.choice([
                    'Значне покращення рухливості суглобів',
                    'Зменшення больового синдрому',
                    'Пацієнт може виконувати складніші вправи',
                    'Покращилася координація рухів',
                    'Зросла витривалість при фізичних навантаженнях'
                ]),
                pain_level=random.randint(1, 7),
                mobility_score=random.randint(60, 95),
                related_program=patient_program,
                recommendations=random.choice([
                    'Продовжити поточну програму',
                    'Збільшити навантаження',
                    'Додати нові вправи',
                    'Зменшити інтенсивність',
                    'Скоригувати частоту занять'
                ])
            )
            progress_logs.append(progress_log)
    
    print(f"Створено: {len(sessions)} сеансів, {len(notes)} нотаток, {len(photos)} фото, {len(progress_logs)} логів прогресу")
    return sessions, notes, photos, progress_logs

def create_notifications(users):
    """Створення сповіщень"""
    print("Створюю сповіщення...")
    
    notifications = []
    
    for user in users:
        if user.user_type in ['patient', 'doctor']:
            # Створюємо 3-8 сповіщень для кожного користувача
            for _ in range(random.randint(3, 8)):
                created_date = timezone.now() - timedelta(days=random.randint(1, 20))
                
                if user.user_type == 'patient':
                    notification_types = [
                        ('appointment', 'Нагадування про прийом', 'У вас заплановано прийом завтра о 14:00'),
                        ('treatment', 'Нове завдання', 'Вам призначено нову програму вправ'),
                        ('progress', 'Відмінний прогрес!', 'Ваші результати покращились на 15%'),
                        ('reminder', 'Час для вправ', 'Не забудьте виконати ранкові вправи'),
                        ('appointment', 'Підтвердження прийому', 'Ваш прийом підтверджено на завтра')
                    ]
                else:  # doctor
                    notification_types = [
                        ('patient', 'Новий пацієнт', 'Вам призначено нового пацієнта: Іван Петренко'),
                        ('appointment', 'Зміна в розкладі', 'Прийом перенесено на 15:30'),
                        ('system', 'Оновлення системи', 'Система буде оновлена сьогодні вночі'),
                        ('patient', 'Скарга пацієнта', 'Пацієнт повідомив про посилення болю'),
                        ('appointment', 'Скасування прийому', 'Пацієнт скасував прийом на завтра')
                    ]
                
                notif_type, title, message = random.choice(notification_types)
                
                notification = Notification.objects.create(
                    recipient=user,
                    notification_type=notif_type,
                    title=title,
                    message=message,
                    is_read=random.choice([True, True, False]),  # Більшість прочитаних
                    created_at=created_date
                )
                notifications.append(notification)
    
    print(f"Створено: {len(notifications)} сповіщень")
    return notifications

def main():
    """Основна функція заповнення даних"""
    print("Початок заповнення бази даних...")
    
    # Видаляємо існуючі дані (крім суперкористувача)
    print("Очищення старих даних...")
    User.objects.filter(is_superuser=False).delete()
    
    # Створюємо користувачів
    admin, doctors, patients = create_users()
    all_users = [admin] + doctors + patients
    
    # Створюємо вправи
    exercises = create_exercise_categories_and_exercises()
    
    # Створюємо програми та прийоми
    programs, appointments = create_programs_and_appointments(doctors, patients, exercises)
    
    # Створюємо консультації
    consultations = create_consultations(doctors, patients)
    
    # Створюємо дані прогресу
    sessions, notes, photos, progress_logs = create_progress_data(patients, doctors, programs)
    
    # Створюємо сповіщення
    notifications = create_notifications(all_users)
    
    print("\n" + "="*50)
    print("ЗАПОВНЕННЯ ЗАВЕРШЕНО!")
    print("="*50)
    print(f"Користувачів: {len(all_users)} (1 адмін, {len(doctors)} лікарів, {len(patients)} пацієнтів)")
    print(f"Вправ: {len(exercises)}")
    print(f"Програм реабілітації: {len(programs)}")
    print(f"Прийомів: {len(appointments)}")
    print(f"Консультацій: {len(consultations)}")
    print(f"Сеансів: {len(sessions)}")
    print(f"Нотаток: {len(notes)}")
    print(f"Фото: {len(photos)}")
    print(f"Логів прогресу: {len(progress_logs)}")
    print(f"Сповіщень: {len(notifications)}")
    print("\nДані для входу:")
    print("Адміністратор: admin / admin123")
    print("Лікар: dr_petrov / doctor123")
    print("Пацієнт: patient_shevchenko / patient123")
    print("="*50)

if __name__ == "__main__":
    main()