# Generated migration for frontend models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('theme', models.CharField(choices=[('light', 'Light Theme'), ('dark', 'Dark Theme'), ('auto', 'Auto (System)')], default='light', max_length=20)),
                ('language', models.CharField(choices=[('uk', 'Ukrainian'), ('en', 'English')], default='uk', max_length=10)),
                ('notifications_enabled', models.BooleanField(default=True)),
                ('dashboard_layout', models.CharField(choices=[('compact', 'Compact'), ('comfortable', 'Comfortable'), ('spacious', 'Spacious')], default='comfortable', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='ui_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Preference',
                'verbose_name_plural': 'User Preferences',
            },
        ),
        migrations.CreateModel(
            name='DashboardWidget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('widget_type', models.CharField(choices=[('appointments', 'Upcoming Appointments'), ('progress', 'Progress Overview'), ('exercises', 'Exercise Schedule'), ('notifications', 'Recent Notifications'), ('statistics', 'Statistics'), ('quick_actions', 'Quick Actions')], max_length=50)),
                ('position', models.PositiveSmallIntegerField(default=0)),
                ('is_enabled', models.BooleanField(default=True)),
                ('settings', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dashboard_widgets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Dashboard Widget',
                'verbose_name_plural': 'Dashboard Widgets',
                'ordering': ['position'],
            },
        ),
        migrations.AddConstraint(
            model_name='dashboardwidget',
            constraint=models.UniqueConstraint(fields=('user', 'widget_type'), name='unique_user_widget_type'),
        ),
    ]