# Generated by Django 5.2.1 on 2025-05-30 19:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('consultation', '0001_initial'),
        ('patients', '0001_initial'),
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='consultation',
            name='doctor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consultations', to='staff.staffprofile'),
        ),
        migrations.AddField(
            model_name='consultation',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consultations', to='patients.patientprofile'),
        ),
        migrations.AddField(
            model_name='consultationnote',
            name='consultation',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='consultation_note', to='consultation.consultation'),
        ),
        migrations.AddField(
            model_name='consultationrecording',
            name='consultation',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='recording', to='consultation.consultation'),
        ),
    ]
