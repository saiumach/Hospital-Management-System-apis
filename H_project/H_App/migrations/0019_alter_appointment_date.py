# Generated by Django 5.1.2 on 2024-11-19 05:16

import H_App.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('H_App', '0018_alter_prescription_date_prescribed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appointment',
            name='date',
            field=models.DateField(default=H_App.models.get_current_date),
        ),
    ]
