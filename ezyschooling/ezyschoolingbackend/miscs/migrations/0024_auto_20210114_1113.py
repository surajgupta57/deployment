# Generated by Django 2.2.10 on 2021-01-14 05:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('miscs', '0023_admissionguidanceprogramme_admissionguidanceprogrammepackage'),
    ]

    operations = [
        migrations.CreateModel(
            name='SurveyChoices',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
            ],
            options={
                'verbose_name': 'Survey Choice',
                'verbose_name_plural': 'Survey Choices',
            },
        ),
        migrations.CreateModel(
            name='SurveyQuestions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.TextField(max_length=1000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Survey Question',
                'verbose_name_plural': 'Survey Questions',
            },
        ),
        migrations.CreateModel(
            name='SurveyResponses',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('answer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='miscs.SurveyChoices')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='miscs.SurveyQuestions')),
            ],
            options={
                'verbose_name': 'Survey Response',
                'verbose_name_plural': 'Survey Responses',
            },
        ),
        migrations.AddField(
            model_name='surveychoices',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='miscs.SurveyQuestions'),
        ),
    ]