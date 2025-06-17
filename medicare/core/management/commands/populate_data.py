"""
Django management command для заповнення бази даних тестовими даними
Використання: python manage.py populate_data
"""
from django.core.management.base import BaseCommand
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Заповнює базу даних тестовими даними'

    def handle(self, *args, **options):
        # Імпорти моделей
        try:
            from patients.models import PatientProfile
            from staff.models import StaffProfile
            from consultation.models import Consultation
            from exercises.models import Exercise, ExerciseCategory
            from notification.models import Notification
            
            self.stdout.write("Початок заповнення бази даних...")
            
            # Не очищаємо існуючі дані, тільки додаємо нові
            self.stdout.write("Додавання нових даних до існуючих...")
            
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
                    'bio': 'Спеціаліст з реабілітації після травм опорно-рухового апарату. Понад 15 років досвіду.'
                },
                {
                    'username': 'dr_ivanova',
                    'email': 'ivanova@medicare.com',
                    'first_name': 'Марія',
                    'last_name': 'Іваненко',
                    'specialization': 'Невролог-реабілітолог',
                    'bio': 'Експерт з неврологічної реабілітації та відновлення після інсульту.'
                },
                {
                    'username': 'dr_kovalenko',
                    'email': 'kovalenko@medicare.com',
                    'first_name': 'Андрій',
                    'last_name': 'Коваленко',
                    'specialization': 'Ортопед-травматолог',
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
                            'bio': doctor_data['bio']
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
                    'date_of_birth': '1985-03-15',
                    'phone_number': '+380501234567',
                    'emergency_contact_name': 'Марія Шевченко',
                    'emergency_contact_phone': '+380509876543',
                    'address': 'м. Київ, вул. Хрещатик, 25',
                    'gender': 'M',
                    'medical_conditions': 'Травма коліна після ДТП у 2023 році. Проходив операцію з відновлення зв\'язок.',
                    'injury_type': 'Травма коліна',
                    'injury_date': '2023-05-15',
                    'diagnosis': 'Розрив зв\'язок колінного суглоба'
                },
                {
                    'username': 'patient_kovalchuk',
                    'email': 'kovalchuk@example.com',
                    'first_name': 'Оксана',
                    'last_name': 'Ковальчук',
                    'date_of_birth': '1975-07-22',
                    'phone_number': '+380502345678',
                    'emergency_contact_name': 'Петро Ковальчук',
                    'emergency_contact_phone': '+380508765432',
                    'address': 'м. Львів, вул. Городоцька, 158',
                    'gender': 'F',
                    'medical_conditions': 'Інсульт у 2023 році. Порушення мовлення та рухових функцій.',
                    'injury_type': 'Інсульт',
                    'injury_date': '2023-08-10',
                    'diagnosis': 'Ішемічний інсульт, парез лівої сторони'
                },
                {
                    'username': 'patient_bondarenko',
                    'email': 'bondarenko@example.com',
                    'first_name': 'Василь',
                    'last_name': 'Бондаренко',
                    'date_of_birth': '1990-11-08',
                    'phone_number': '+380503456789',
                    'emergency_contact_name': 'Ольга Бондаренко',
                    'emergency_contact_phone': '+380507654321',
                    'address': 'м. Дніпро, пр. Героїв, 42',
                    'gender': 'M',
                    'medical_conditions': 'Хронічний біль у спині через сидячу роботу. Сколіоз.',
                    'injury_type': 'Сколіоз',
                    'injury_date': '2022-01-01',
                    'diagnosis': 'Сколіоз II ступеня, остеохондроз поперекового відділу'
                },
                {
                    'username': 'patient_lysenko',
                    'email': 'lysenko@example.com',
                    'first_name': 'Ірина',
                    'last_name': 'Лисенко',
                    'date_of_birth': '1988-12-03',
                    'phone_number': '+380504567890',
                    'emergency_contact_name': 'Ігор Лисенко',
                    'emergency_contact_phone': '+380506543210',
                    'address': 'м. Одеса, вул. Дерибасівська, 12',
                    'gender': 'F',
                    'medical_conditions': 'Перелом правої руки у 2024 році.',
                    'injury_type': 'Перелом променевої кістки',
                    'injury_date': '2024-02-20',
                    'diagnosis': 'Закритий перелом променевої кістки правої руки'
                },
                {
                    'username': 'patient_moroz',
                    'email': 'moroz@example.com',
                    'first_name': 'Віктор',
                    'last_name': 'Мороз',
                    'date_of_birth': '1980-04-17',
                    'phone_number': '+380505678901',
                    'emergency_contact_name': 'Тетяна Мороз',
                    'emergency_contact_phone': '+380505432109',
                    'address': 'м. Харків, вул. Сумська, 78',
                    'gender': 'M',
                    'medical_conditions': 'Артрит колінних суглобів.',
                    'injury_type': 'Артрит',
                    'injury_date': '2021-06-01',
                    'diagnosis': 'Ревматоїдний артрит колінних суглобів'
                }
            ]
            
            patients = []
            for patient_data in patients_data:
                # Додаємо номер телефону до користувача
                user, created = User.objects.get_or_create(
                    username=patient_data['username'],
                    defaults={
                        'email': patient_data['email'],
                        'first_name': patient_data['first_name'],
                        'last_name': patient_data['last_name'],
                        'user_type': 'patient',
                        'phone_number': patient_data['phone_number'],
                        'password': make_password('patient123'),
                        'date_joined': timezone.now() - timedelta(days=random.randint(10, 50))
                    }
                )
                
                if created or not hasattr(user, 'patient_profile'):
                    patient_profile, _ = PatientProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'date_of_birth': datetime.strptime(patient_data['date_of_birth'], '%Y-%m-%d').date(),
                            'gender': patient_data['gender'],
                            'address': patient_data['address'],
                            'emergency_contact_name': patient_data['emergency_contact_name'],
                            'emergency_contact_phone': patient_data['emergency_contact_phone']
                        }
                    )
                    
                    # Створюємо медичну історію
                    from patients.models import MedicalHistory, RehabilitationHistory
                    medical_history, _ = MedicalHistory.objects.get_or_create(
                        patient=patient_profile,
                        defaults={
                            'conditions': patient_data['medical_conditions']
                        }
                    )
                    
                    # Створюємо історію реабілітації
                    rehab_history, _ = RehabilitationHistory.objects.get_or_create(
                        patient=patient_profile,
                        injury_type=patient_data['injury_type'],
                        defaults={
                            'injury_date': datetime.strptime(patient_data['injury_date'], '%Y-%m-%d').date(),
                            'diagnosis': patient_data['diagnosis'],
                            'notes': f"Пацієнт {user.get_full_name()}, {patient_data['diagnosis']}",
                            'doctor': doctors[0].staff_profile if doctors else None
                        }
                    )
                
                patients.append(user)
            
            self.stdout.write(f"Створено користувачів: 1 адмін, {len(doctors)} лікарів, {len(patients)} пацієнтів")
            
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
            
            # Створюємо рівні складності
            from exercises.models import DifficultyLevel, BodyPart
            
            difficulty_levels = [
                {'name': 'Початковий', 'value': 1},
                {'name': 'Середній', 'value': 2},
                {'name': 'Просунутий', 'value': 3}
            ]
            
            difficulties = []
            for diff_data in difficulty_levels:
                difficulty, _ = DifficultyLevel.objects.get_or_create(
                    value=diff_data['value'],
                    defaults={'name': diff_data['name']}
                )
                difficulties.append(difficulty)
            
            # Створюємо частини тіла
            body_parts_data = ['Шия', 'Спина', 'Ноги', 'Руки', 'Корпус', 'Коліна']
            body_parts = []
            for part_name in body_parts_data:
                body_part, _ = BodyPart.objects.get_or_create(name=part_name)
                body_parts.append(body_part)
            
            # Створюємо вправи
            exercises_data = [
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
                {
                    'title': 'Ходьба на місці',
                    'description': 'М\'яке кардіо навантаження',
                    'instructions': '1. Станьте прямо\n2. Піднімайте коліна по черзі\n3. Рухайте руками\n4. Продовжуйте 5-10 хвилин',
                    'category': categories[2],
                    'difficulty': 'beginner',
                    'duration': 10
                },
                {
                    'title': 'Стояння на одній нозі',
                    'description': 'Покращення рівноваги та координації',
                    'instructions': '1. Станьте на одну ногу\n2. Тримайте рівновагу 30 секунд\n3. Поміняйте ногу\n4. Повторіть 3 рази',
                    'category': categories[3],
                    'difficulty': 'intermediate',
                    'duration': 5
                },
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
            
            self.stdout.write(f"Створено: {len(categories)} категорій вправ, {len(exercises)} вправ")
            
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
            
            self.stdout.write(f"Створено: {len(consultations)} консультацій")
            
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
            
            self.stdout.write(f"Створено: {len(notifications)} сповіщень")
            
            self.stdout.write("\nЗАПОВНЕННЯ ЗАВЕРШЕНО!")
            self.stdout.write("="*50)
            self.stdout.write("Дані для входу:")
            self.stdout.write("Адміністратор: admin / admin123")
            self.stdout.write("Лікар: dr_petrov / doctor123")
            self.stdout.write("Пацієнт: patient_shevchenko / patient123")
            self.stdout.write("="*50)
            
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f"Помилка імпорту: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Помилка: {e}"))