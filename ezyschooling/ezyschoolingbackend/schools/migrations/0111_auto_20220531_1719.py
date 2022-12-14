# Generated by Django 2.2.10 on 2022-05-31 11:49

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import schools.utils


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0110_auto_20220425_1344'),
    ]

    operations = [
        migrations.CreateModel(
            name='BoardingSchoolInfrastructureHead',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(max_length=80)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Boarding School Infrastruture Type',
                'verbose_name_plural': 'Boarding School Infrastruture Types',
            },
        ),
        migrations.CreateModel(
            name='BoardingSchoolInfrastrutureImages',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, null=True, upload_to=schools.utils.boarding_school_infra_image_upload_path)),
                ('visible', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Boarding School Infrastruture Image',
                'verbose_name_plural': 'Boarding School Infrastruture Images',
            },
        ),
        migrations.CreateModel(
            name='FoodCategories',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25)),
                ('type', models.CharField(blank=True, choices=[('Veg', 'Veg'), ('Non-Veg', 'Non-Veg'), ('Jain', 'Jain'), ('Egg', 'Egg'), ('Vegan', 'Vegan')], default='Veg', max_length=25, null=True)),
            ],
            options={
                'verbose_name': 'Food Type',
                'verbose_name_plural': 'Food Types',
            },
        ),
        migrations.CreateModel(
            name='ScheduleTimings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('start_time', models.TimeField(blank=True, null=True)),
                ('end_time', models.TimeField(blank=True, null=True)),
                ('duration', models.DurationField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Daywise Schedule Time/Parameter',
                'verbose_name_plural': 'Daywise Schedule Times/Parameters',
            },
        ),
        migrations.AddField(
            model_name='feestructure',
            name='note',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='schoolprofile',
            name='boarding_school',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AddField(
            model_name='schoolprofile',
            name='scholarship_program',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.CreateModel(
            name='SchoolAlumni',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Provide Full name of alumni', max_length=100)),
                ('image', models.ImageField(blank=True, default='alumni/images/default.png', null=True, upload_to=schools.utils.alumni_image_upload_path)),
                ('passing_year', models.PositiveIntegerField(help_text='ex: 1988 or 1999 or 2004 or 2015 ')),
                ('current_designation', models.CharField(blank=True, help_text='Provide Designation of alumni', max_length=100, null=True)),
                ('featured', models.BooleanField(default=False)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='schools.SchoolProfile')),
            ],
            options={
                'verbose_name': 'School Alumni',
                'verbose_name_plural': 'School Alumni List',
            },
        ),
        migrations.CreateModel(
            name='DaywiseSchedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(blank=True, choices=[('Weekdays', 'Weekdays'), ('Weekends', 'Weekends')], default='Weekdays', max_length=50, null=True)),
                ('session', models.CharField(blank=True, max_length=20, null=True)),
                ('ending_class', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='daywise_class_ranage_ending', to='schools.SchoolClasses')),
                ('school', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='schools.SchoolProfile')),
                ('starting_class', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='daywise_class_ranage_starting', to='schools.SchoolClasses')),
                ('values', models.ManyToManyField(blank=True, to='schools.ScheduleTimings')),
            ],
            options={
                'verbose_name': 'Daywise Schedule',
                'verbose_name_plural': 'Daywise Schedules',
            },
        ),
        migrations.CreateModel(
            name='BoardingSchoolInfrastructure',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(blank=True, null=True)),
                ('related_images', models.ManyToManyField(blank=True, to='schools.BoardingSchoolInfrastrutureImages')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='schools.SchoolProfile')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='schools.BoardingSchoolInfrastructureHead')),
            ],
            options={
                'verbose_name': 'Boarding School Infrastruture',
                'verbose_name_plural': 'Boarding Schools Infrastruture',
            },
        ),
        migrations.CreateModel(
            name='BoardingSchoolExtend',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pre_post_admission_process', models.TextField(blank=True, null=True)),
                ('withdrawl_policy', models.TextField(blank=True, null=True)),
                ('food_details', models.TextField(blank=True, null=True)),
                ('faq_related_data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
                ('extended_school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='schools.SchoolProfile')),
                ('food_option', models.ManyToManyField(blank=True, to='schools.FoodCategories')),
                ('infrastruture', models.ManyToManyField(blank=True, related_name='school_infra', to='schools.BoardingSchoolInfrastructure')),
                ('weekday_schedule', models.ManyToManyField(blank=True, related_name='daywise_weekday_schedule', to='schools.DaywiseSchedule')),
                ('weekend_schedule', models.ManyToManyField(blank=True, related_name='daywise_weekend_schedule', to='schools.DaywiseSchedule')),
            ],
            options={
                'verbose_name': 'Boarding School Extended Profile',
                'verbose_name_plural': 'Boarding School Extended Profiles',
            },
        ),
    ]
