# Generated by Django 5.2.1 on 2025-05-30 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('report_type', models.CharField(choices=[('patient_progress', 'Patient Progress'), ('program_completion', 'Program Completion'), ('doctor_activity', 'Doctor Activity'), ('survey_results', 'Survey Results'), ('system_usage', 'System Usage'), ('custom', 'Custom Report')], max_length=20)),
                ('description', models.TextField(blank=True, null=True)),
                ('parameters', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Report',
                'verbose_name_plural': 'Reports',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ReportExport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='report_exports/')),
                ('format', models.CharField(choices=[('pdf', 'PDF'), ('csv', 'CSV'), ('excel', 'Excel')], max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Report Export',
                'verbose_name_plural': 'Report Exports',
                'ordering': ['-created_at'],
            },
        ),
    ]
