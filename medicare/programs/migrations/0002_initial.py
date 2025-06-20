# Generated by Django 5.2.1 on 2025-05-30 19:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patients', '0002_initial'),
        ('programs', '0001_initial'),
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='rehabilitationprogram',
            name='doctor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assigned_programs', to='staff.staffprofile'),
        ),
        migrations.AddField(
            model_name='rehabilitationprogram',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rehabilitation_programs', to='patients.patientprofile'),
        ),
        migrations.AddField(
            model_name='programday',
            name='program',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='program_days', to='programs.rehabilitationprogram'),
        ),
        migrations.AlterUniqueTogether(
            name='programday',
            unique_together={('program', 'day_number')},
        ),
    ]
