from django.core.management.base import BaseCommand
from exercises.models import BodyPart, ExerciseCategory, DifficultyLevel


class Command(BaseCommand):
    help = 'Populate database with sample body parts, categories, and difficulty levels'

    def handle(self, *args, **options):
        # Create Body Parts
        body_parts = [
            'Шия',
            'Плечі',
            'Руки',
            'Груди',
            'Спина',
            'Живіт',
            'Поперек',
            'Стегна',
            'Коліна',
            'Гомілки',
            'Стопи',
            'Кисті рук',
        ]
        
        created_body_parts = 0
        for part_name in body_parts:
            body_part, created = BodyPart.objects.get_or_create(name=part_name)
            if created:
                created_body_parts += 1
                self.stdout.write(f'Створено частину тіла: {part_name}')
        
        # Create Exercise Categories
        categories = [
            ('Розтяжка', 'Вправи для покращення гнучкості та розтяжки м\'язів'),
            ('Силові', 'Вправи для зміцнення м\'язів'),
            ('Кардіо', 'Аеробні вправи для покращення роботи серцево-судинної системи'),
            ('Баланс', 'Вправи для покращення координації та рівноваги'),
            ('Реабілітація', 'Спеціальні вправи для відновлення після травм'),
            ('Дихальні', 'Вправи для покращення дихання'),
            ('Постуральні', 'Вправи для покращення постави'),
            ('Мобільність', 'Вправи для покращення рухливості суглобів'),
        ]
        
        created_categories = 0
        for cat_name, cat_desc in categories:
            category, created = ExerciseCategory.objects.get_or_create(
                name=cat_name,
                defaults={'description': cat_desc}
            )
            if created:
                created_categories += 1
                self.stdout.write(f'Створено категорію: {cat_name}')
        
        # Create Difficulty Levels
        difficulty_levels = [
            ('Початковий', 1),
            ('Легкий', 2),
            ('Помірний', 3),
            ('Середній', 4),
            ('Складний', 5),
        ]
        
        created_difficulties = 0
        for diff_name, diff_value in difficulty_levels:
            difficulty, created = DifficultyLevel.objects.get_or_create(
                value=diff_value,
                defaults={'name': diff_name}
            )
            if created:
                created_difficulties += 1
                self.stdout.write(f'Створено рівень складності: {diff_name} ({diff_value})')
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nГотово! Створено:\n'
                f'- Частин тіла: {created_body_parts}\n'
                f'- Категорій: {created_categories}\n'
                f'- Рівнів складності: {created_difficulties}'
            )
        )
        
        # Show current totals
        total_body_parts = BodyPart.objects.count()
        total_categories = ExerciseCategory.objects.count()
        total_difficulties = DifficultyLevel.objects.count()
        
        self.stdout.write(
            f'\nВсього в базі даних:\n'
            f'- Частин тіла: {total_body_parts}\n'
            f'- Категорій: {total_categories}\n'
            f'- Рівнів складності: {total_difficulties}'
        )