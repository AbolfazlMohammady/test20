# Generated by Django 5.0.6 on 2025-05-18 19:47

import core.valirations
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_user_national_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='national_id',
            field=models.CharField(blank=True, max_length=10, null=True, unique=True, validators=[core.valirations.validate_national_code], verbose_name='کد ملی'),
        ),
    ]
