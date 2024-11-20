# Generated by Django 5.1.2 on 2024-11-17 12:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('H_App', '0004_appointment_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='prescription',
            name='appointment',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='prescriptions_as_appointment', to='H_App.appointment'),
        ),
        migrations.AlterField(
            model_name='prescription',
            name='dosage',
            field=models.CharField(max_length=100),
        ),
    ]
