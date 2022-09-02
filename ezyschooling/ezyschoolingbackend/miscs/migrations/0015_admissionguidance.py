# Generated by Django 2.2.10 on 2020-09-21 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('miscs', '0014_carousel_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdmissionGuidance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parent_name', models.CharField(max_length=200)),
                ('phone', models.CharField(max_length=30)),
                ('email', models.EmailField(max_length=254)),
                ('dob', models.DateField(verbose_name="Child's Date of Birth")),
                ('target_region', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Admission Guidance Registration',
                'verbose_name_plural': 'Admission Guidance Registrations',
            },
        ),
    ]