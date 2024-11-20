# Generated by Django 5.1.2 on 2024-11-18 13:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('H_App', '0013_prescription_afternoon_prescription_evening_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='prescription',
            name='appointment_id',
        ),
        migrations.RemoveField(
            model_name='prescription',
            name='date_prescribed',
        ),
        migrations.AddField(
            model_name='prescription',
            name='medicines',
            field=models.ManyToManyField(related_name='prescriptions', to='H_App.medicine'),
        ),
    ]
