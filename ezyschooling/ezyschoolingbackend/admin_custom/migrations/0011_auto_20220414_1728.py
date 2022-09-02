# Generated by Django 2.2.10 on 2022-04-14 11:58

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('admin_custom', '0010_auto_20220413_1300'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolDashboardMasterActionCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'verbose_name': 'School Action Category',
                'verbose_name_plural': 'School Action Categories',
            },
        ),
        migrations.AlterModelOptions(
            name='actionsection',
            options={'verbose_name': 'Action', 'verbose_name_plural': 'Actions'},
        ),
        migrations.AlterModelOptions(
            name='admissiondonedata',
            options={'verbose_name': 'Admission Done', 'verbose_name_plural': 'Admissions Done'},
        ),
        migrations.AlterModelOptions(
            name='commentsection',
            options={'verbose_name': 'Counsellor Comment', 'verbose_name_plural': 'Counsellor Comments'},
        ),
        migrations.AlterModelOptions(
            name='counselingaction',
            options={'verbose_name': 'Counsellor Action', 'verbose_name_plural': 'Counsellor Actions'},
        ),
        migrations.AlterModelOptions(
            name='counsellordailycallrecord',
            options={'verbose_name': 'Counsellor Daily Call Reocord', 'verbose_name_plural': 'Counsellors Daily Call Reocord'},
        ),
        migrations.AlterModelOptions(
            name='counselorcadminuser',
            options={'verbose_name': 'Counsellor User', 'verbose_name_plural': 'Counsellor Users'},
        ),
        migrations.AlterModelOptions(
            name='leadgenerated',
            options={'verbose_name': 'Lead Generated', 'verbose_name_plural': 'Leads Generated'},
        ),
        migrations.AlterModelOptions(
            name='masteractioncategory',
            options={'verbose_name': 'Action Category', 'verbose_name_plural': 'Action Categories'},
        ),
        migrations.AlterModelOptions(
            name='subactionsection',
            options={'verbose_name': 'Sub Action', 'verbose_name_plural': 'Sub Actions'},
        ),
        migrations.AlterModelOptions(
            name='visitscheduledata',
            options={'verbose_name': 'Visit Scheduled', 'verbose_name_plural': 'Visits Scheduled'},
        ),
        migrations.CreateModel(
            name='SchoolDashboardActionSection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(blank=True, null=True)),
                ('requires_datetime', models.BooleanField(default=False)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='school_action_type', to='admin_custom.SchoolDashboardMasterActionCategory')),
            ],
            options={
                'verbose_name': 'School Action',
                'verbose_name_plural': 'School Actions',
            },
        ),
        migrations.CreateModel(
            name='SchoolCommentSection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(max_length=500)),
                ('timestamp', models.DateTimeField(auto_now_add=True, null=True)),
                ('action', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='counselling_action_relation_c', to='admin_custom.CounselingAction', verbose_name="Counsellor's Action(C)")),
                ('counsellor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_custom.CounselorCAdminUser', verbose_name='counseling User')),
                ('school', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.SchoolProfile')),
            ],
            options={
                'verbose_name': 'School Comment',
                'verbose_name_plural': 'School Comments',
            },
        ),
        migrations.CreateModel(
            name='SchoolAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scheduled_time', models.DateTimeField(blank=True, null=True)),
                ('first_action', django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict, null=True)),
                ('action_created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('action_updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('action', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_custom.SchoolDashboardActionSection')),
                ('counsellor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_custom.CounselorCAdminUser', verbose_name='Counsellor User')),
                ('school', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.SchoolProfile')),
            ],
            options={
                'verbose_name': 'School Action',
                'verbose_name_plural': 'School Actions',
            },
        ),
    ]
