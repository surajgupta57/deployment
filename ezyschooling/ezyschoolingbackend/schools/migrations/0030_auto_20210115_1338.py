# Generated by Django 2.2.10 on 2021-01-15 08:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0029_auto_20201225_1149'),
    ]

    operations = [
        migrations.AddField(
            model_name='admmissionopenclasses',
            name='last_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='admmissionopenclasses',
            name='session',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.CreateModel(
            name='SchoolAdmissionFormFee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('class_relation', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='schools.SchoolClasses')),
                ('school_relation', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='schools.SchoolProfile')),
            ],
            options={
                'verbose_name': 'School Admission Form Fee',
                'verbose_name_plural': 'School Admission Form Fee',
            },
        ),
    ]