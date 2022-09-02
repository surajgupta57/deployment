# Generated by Django 2.2.10 on 2020-04-07 12:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('analatics', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClickLogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_time', models.DateTimeField(auto_now_add=True)),
                ('object_id', models.TextField(blank=True, null=True, verbose_name='object id')),
                ('action_flag', models.PositiveSmallIntegerField(choices=[(1, 'Addition'), (2, 'Change'), (3, 'Deletion'), (4, 'Read')], verbose_name='action flag')),
                ('path', models.CharField(blank=True, max_length=1000, null=True)),
                ('client_ip', models.CharField(blank=True, max_length=200, null=True)),
                ('is_mobile', models.BooleanField(blank=True, default=False, null=True)),
                ('is_tablet', models.BooleanField(blank=True, default=False, null=True)),
                ('is_touch_capable', models.BooleanField(blank=True, default=False, null=True)),
                ('is_pc', models.BooleanField(blank=True, default=False, null=True)),
                ('is_bot', models.BooleanField(blank=True, default=False, null=True)),
                ('browser_family', models.CharField(blank=True, max_length=100, null=True)),
                ('browser_version', models.CharField(blank=True, max_length=100, null=True)),
                ('browser_version_string', models.CharField(blank=True, max_length=100, null=True)),
                ('os_family', models.CharField(blank=True, max_length=100, null=True)),
                ('os_version', models.CharField(blank=True, max_length=100, null=True)),
                ('os_version_string', models.CharField(blank=True, max_length=100, null=True)),
                ('device_family', models.CharField(blank=True, max_length=100, null=True)),
                ('action_message', models.TextField(blank=True, verbose_name='action message')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.ContentType', verbose_name='content type')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'ordering': ['-action_time'],
            },
        ),
    ]