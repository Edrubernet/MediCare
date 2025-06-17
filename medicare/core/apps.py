from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Основні функції системи'
    
    def ready(self):
        """Ініціалізація додатку при старті."""
        pass