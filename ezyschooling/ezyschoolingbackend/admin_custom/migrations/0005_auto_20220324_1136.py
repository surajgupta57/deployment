# Generated by Django 2.2.10 on 2022-03-24 06:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0104_auto_20220324_1136'),
        ('childs', '0011_child_illness'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('admin_custom', '0004_auto_20220305_2021'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionSection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField()),
            ],
        ),
        migrations.CreateModel(
            name='MasterActionCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CounselingAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enquiry_scheduled_time', models.DateTimeField(blank=True, null=True)),
                ('child_scheduled_time', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('child_action', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_custom.ActionSection')),
                ('child_data', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='child_data', to='childs.Child', verbose_name='Child Data')),
                ('counseling_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='counseling_user_action', to='admin_custom.CounselorCAdminUser', verbose_name='Counseling Action User')),
                ('enquiry_action', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='enquiry_action', to='admin_custom.ActionSection')),
                ('enquiry_data', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='enquiry_data', to='schools.SchoolEnquiry')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_for_counseling', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
        migrations.CreateModel(
            name='CommentSection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(max_length=500)),
                ('timestamp', models.DateTimeField(auto_now_add=True, null=True)),
                ('child', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='comment_wrt_child', to='childs.Child', verbose_name="Users' Child")),
                ('counseling', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='counseling_to_user', to='admin_custom.CounselorCAdminUser', verbose_name='counseling User')),
                ('enquiry_comment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='enquiry_comment_data', to='schools.SchoolEnquiry')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_counseling_comment', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Comment Section',
                'verbose_name_plural': 'Comment Section',
            },
        ),
        migrations.AddField(
            model_name='actionsection',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='enquiry_action_type', to='admin_custom.MasterActionCategory'),
        ),
    ]
