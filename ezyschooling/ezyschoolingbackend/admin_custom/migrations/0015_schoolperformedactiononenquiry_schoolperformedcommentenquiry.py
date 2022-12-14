# Generated by Django 2.2.10 on 2022-04-26 08:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('admin_custom', '0014_auto_20220418_1340'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolPerformedCommentEnquiry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True, null=True)),
                ('enquiry', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.SchoolEnquiry')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SchoolPerformedActionOnEnquiry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scheduled_time', models.DateTimeField(blank=True, null=True)),
                ('action_created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('action_updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('action', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_custom.SchoolDashboardActionSection')),
                ('enquiry', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.SchoolEnquiry')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
