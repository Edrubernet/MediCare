# Generated by Django 5.2.1 on 2025-05-30 19:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('patients', '0002_initial'),
        ('progress', '0001_initial'),
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='patientnote',
            name='doctor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='patient_notes', to='staff.staffprofile'),
        ),
        migrations.AddField(
            model_name='patientnote',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='patients.patientprofile'),
        ),
        migrations.AddField(
            model_name='progressphoto',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress_photos', to='patients.patientprofile'),
        ),
    ]
