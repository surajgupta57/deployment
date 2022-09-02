# Generated by Django 2.2.10 on 2020-10-13 04:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0020_auto_20200924_2352'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityTypeAutocomplete',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'School Activity Type Autocomplete Data',
                'verbose_name_plural': 'School Activity Type Autocomplete Data',
            },
        ),
        migrations.CreateModel(
            name='ActivityAutocomplete',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('activity_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='schools.ActivityTypeAutocomplete')),
            ],
            options={
                'verbose_name': 'School Activity Autocomplete Data',
                'verbose_name_plural': 'School Activity Autocomplete Data',
            },
        ),
    ]
