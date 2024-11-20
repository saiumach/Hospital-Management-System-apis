# Generated by Django 5.1.2 on 2024-11-18 10:43

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('H_App', '0010_remove_prescription_appointment_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prescription',
            name='appointment_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
