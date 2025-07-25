# Generated by Django 5.0.6 on 2025-05-12 13:16

import django.db.models.deletion
import django_jalali.db.models
import project.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LayerType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='نوع لایه')),
            ],
            options={
                'verbose_name': 'نوع لایه',
                'verbose_name_plural': 'انواع لایه\u200cها',
            },
        ),
        migrations.CreateModel(
            name='StructureType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='نوع اَبنیه')),
            ],
            options={
                'verbose_name': 'نوع اَبنیه',
                'verbose_name_plural': 'انواع اَبنیه ها',
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='نام پروژه')),
                ('start_date', django_jalali.db.models.jDateField(blank=True, null=True, verbose_name='تاریخ شروع')),
                ('end_date', django_jalali.db.models.jDateField(blank=True, null=True, verbose_name='تاریخ پایان')),
                ('budget', models.DecimalField(blank=True, decimal_places=0, max_digits=50, null=True, verbose_name='بودجه')),
                ('created_at', django_jalali.db.models.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', django_jalali.db.models.jDateTimeField(auto_now=True, verbose_name='تاریخ به\u200cروزرسانی')),
                ('distance', models.PositiveBigIntegerField(help_text='فاصله پروژه به کیلومتر', verbose_name='فاصله (کیلومتر)')),
                ('width', models.PositiveBigIntegerField(help_text='عرض پروژه به متر', verbose_name='عرض (متر)')),
                ('start_kilometer', models.PositiveBigIntegerField(help_text='کیلومتر شروع پروژه', verbose_name='کیلومتر شروع')),
                ('end_kilometer', models.PositiveBigIntegerField(help_text='کیلومتر پایان پروژه', verbose_name='کیلومتر پایان')),
                ('profile_file', models.FileField(blank=True, null=True, upload_to='project_profiles/', validators=[project.validators.validate_excel_file], verbose_name='پروفیل')),
                ('project_manager', models.ForeignKey(blank=True, help_text='مدیر پروژه را انتخاب کنید', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='managed_projects', to=settings.AUTH_USER_MODEL, verbose_name='مدیر پروژه')),
                ('quality_control_manager', models.ForeignKey(blank=True, help_text='مدیر کنترل کیفیت را انتخاب کنید', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='qc_projects', to=settings.AUTH_USER_MODEL, verbose_name='مدیر کنترل کیفیت')),
                ('technical_manager', models.ForeignKey(blank=True, help_text='مدیر فنی را انتخاب کنید', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='technical_projects', to=settings.AUTH_USER_MODEL, verbose_name='مدیر فنی')),
            ],
            options={
                'verbose_name': 'پروژه',
                'verbose_name_plural': 'پروژه\u200cها',
            },
        ),
        migrations.CreateModel(
            name='ProjectEx',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_joined', django_jalali.db.models.jDateField(verbose_name='تاریخ ورود')),
                ('date_left', django_jalali.db.models.jDateField(blank=True, null=True, verbose_name='تاریخ خروج')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project', verbose_name='پروژه')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='کارشناس')),
            ],
            options={
                'verbose_name': 'کارشناس پروژه',
                'verbose_name_plural': 'کارشناسان پروژه',
                'ordering': ['-date_joined'],
                'unique_together': {('user', 'project')},
            },
        ),
        migrations.AddField(
            model_name='project',
            name='project_experts',
            field=models.ManyToManyField(blank=True, help_text='کارشناسان پروژه را انتخاب کنید', related_name='project_experts', through='project.ProjectEx', to=settings.AUTH_USER_MODEL, verbose_name='کارشناسان پروژه'),
        ),
        migrations.CreateModel(
            name='ProjectLayer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thickness_cm', models.PositiveSmallIntegerField(verbose_name='ضخامت (سانتی\u200cمتر)')),
                ('order_from_top', models.PositiveSmallIntegerField(verbose_name='ترتیب از بالا')),
                ('status', models.PositiveSmallIntegerField(choices=[(0, 'شروع نشده'), (1, 'در حال انجام'), (2, 'تکمیل شده'), (3, 'متوقف شده'), (4, 'لغو شده')], default=0, help_text='وضعیت لایه را انتخاب کنید', verbose_name='وضعیت')),
                ('layer_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='project.layertype', verbose_name='نوع لایه')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='project.project', verbose_name='پروژه')),
            ],
            options={
                'verbose_name': 'لایه پروژه',
                'verbose_name_plural': 'لایه\u200cهای پروژه',
                'ordering': ['order_from_top'],
                'unique_together': {('project', 'layer_type')},
            },
        ),
        
    ]
