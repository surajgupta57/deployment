# Generated by Django 2.2.10 on 2021-03-16 05:56

from django.db import migrations, models
import django.db.models.deletion
import schools.utils


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0039_auto_20210311_1751'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppliedSchoolSelectedCsv',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('csv_file', models.FileField(blank=True, null=True, upload_to=schools.utils.school_selected_csv_upload_path)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('school_relation', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='schools.SchoolProfile')),
            ],
            options={
                'verbose_name': 'CSV Uploaded From School',
                'verbose_name_plural': "CSV'S Uploaded From Schools",
            },
        ),
        migrations.CreateModel(
            name='SelectedStudentFromCsv',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('child_name', models.CharField(blank=True, max_length=255, null=True)),
                ('father_name', models.CharField(blank=True, max_length=255, null=True)),
                ('mother_name', models.CharField(blank=True, max_length=255, null=True)),
                ('guardian_name', models.CharField(blank=True, max_length=255, null=True)),
                ('receipt_id', models.CharField(blank=True, max_length=255, null=True)),
                ('school_csv_name', models.CharField(blank=True, max_length=400, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='schools.AppliedSchoolSelectedCsv')),
                ('school_relation', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='schools.SchoolProfile')),
            ],
        ),
    ]
