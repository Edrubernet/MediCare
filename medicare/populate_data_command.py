"""
Команда Django для заповнення бази даних тестовими даними
Використання: python manage.py shell < populate_data_command.py
"""

from datetime import datetime, timedelta, time
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
import random

User = get_user_model()

# Імпорти моделей
try:
    from patients.models import PatientProfile
    from staff.models import StaffProfile
    from consultation.models import Consultation
    from programs.models import RehabilitationProgram, Appointment, ProgressLog, ProgramDay, ProgramExercise
    from exercises.models import Exercise, ExerciseCategory
    from notification.models import Notification
    from progress.models import Session, Note, Photo
    
    print("Імпорти успішні, початок заповнення...")
    
    # Видаляємо існуючі дані (крім суперкористувача)
    print("Очищення старих даних...")
    User.objects.filter(is_superuser=False).delete()
    
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
            'date_joined': timezone.now() - timedelta(days=30)
        }
    )
    
    # Створюємо лікарів
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
    
    # Створюємо пацієнтів
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
    
    print(f"Створено користувачів: 1 адмін, {len(doctors)} лікарів, {len(patients)} пацієнтів")
    
    # Створюємо категорії вправ
    categories_data = [
        {'name': 'Розтяжка', 'description': 'Вправи для покращення гнучкості та розтяжки м\'язів'},
        {'name': 'Силові вправи', 'description': 'Вправи для зміцнення м\'язів'},
        {'name': 'Кардіо', 'description': 'Вправи для покращення серцево-судинної системи'},
        {'name': 'Баланс', 'description': 'Вправи для покращення координації та рівноваги'},
        {'name': 'Дихальні вправи', 'description': 'Вправи для покращення дихання та релаксації'}
    ]
    
    categories = []
    for cat_data in categories_data:
        category, _ = ExerciseCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        categories.append(category)
    
    # Створюємо вправи
    exercises_data = [
        {
            'title': 'Розтяжка шийних м\'язів',
            'description': 'М\'яка розтяжка м\'язів шиї для зняття напруження',
            'instructions': '1. Сідьте прямо\\n2. Повільно нахиліть голову вправо\\n3. Тримайте 15 секунд\\n4. Повторіть в інший бік',
            'category': categories[0],
            'difficulty': 'beginner',
            'duration': 5
        },
        {
            'title': 'Розтяжка спини',
            'description': 'Розтяжка м\'язів спини для зменшення болю',
            'instructions': '1. Лягте на спину\\n2. Підтягніть коліна до грудей\\n3. Тримайте 20 секунд\\n4. Повторіть 3 рази',
            'category': categories[0],
            'difficulty': 'beginner',
            'duration': 10
        },
        {
            'title': 'Планка',
            'description': 'Базова вправа для зміцнення м\'язів корсету',
            'instructions': '1. Станьте у положення планки\\n2. Тримайте тіло прямо\\n3. Утримуйте позицію 30 секунд\\n4. Відпочиньте та повторіть',
            'category': categories[1],
            'difficulty': 'intermediate',
            'duration': 15
        },
        {
            'title': 'Присідання',
            'description': 'Зміцнення м\'язів ніг та сідниць',
            'instructions': '1. Поставте ноги на ширині плечей\\n2. Повільно присядьте\\n3. Встаньте у вихідне положення\\n4. Повторіть 10-15 разів',
            'category': categories[1],
            'difficulty': 'beginner',
            'duration': 10
        },
        {
            'title': 'Ходьба на місці',
            'description': 'М\'яке кардіо навантаження',
            'instructions': '1. Станьте прямо\\n2. Піднімайте коліна по черзі\\n3. Рухайте руками\\n4. Продовжуйте 5-10 хвилин',
            'category': categories[2],
            'difficulty': 'beginner',
            'duration': 10
        },
        {
            'title': 'Стояння на одній нозі',
            'description': 'Покращення рівноваги та координації',
            'instructions': '1. Станьте на одну ногу\\n2. Тримайте рівновагу 30 секунд\\n3. Поміняйте ногу\\n4. Повторіть 3 рази',
            'category': categories[3],
            'difficulty': 'intermediate',
            'duration': 5
        },
        {
            'title': 'Глибоке дихання',
            'description': 'Техніка релаксації та покращення дихання',
            'instructions': '1. Сядьте зручно\\n2. Вдихніть повільно через ніс 4 секунди\\n3. Затримайте дихання на 4 секунди\\n4. Видихніть через рот 6 секунд',
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
    
    print(f"Створено: {len(categories)} категорій вправ, {len(exercises)} вправ")
    
    # Створюємо консультації для кожного пацієнта
    consultations = []
    for patient in patients:
        doctor = random.choice(doctors)
        
        # 2-4 консультації для кожного пацієнта
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
    
    # Створюємо сповіщення
    notifications = []
    all_users = [admin] + doctors + patients
    
    for user in all_users:
        if user.user_type in ['patient', 'doctor']:
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
                        ('patient', 'Новий пацієнт', 'Вам призначено нового пацієнта'),
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
                    is_read=random.choice([True, True, False]),
                    created_at=created_date
                )
                notifications.append(notification)
    
    print(f"Створено: {len(notifications)} сповіщень")
    
    print("\\nЗАПОВНЕННЯ ЗАВЕРШЕНО!")
    print("="*50)
    print("Дані для входу:")
    print("Адміністратор: admin / admin123")
    print("Лікар: dr_petrov / doctor123")
    print("Пацієнт: patient_shevchenko / patient123")
    print("="*50)
    
except ImportError as e:
    print(f"Помилка імпорту: {e}")
    print("Деякі моделі можуть бути недоступні")
except Exception as e:
    print(f"Помилка: {e}")