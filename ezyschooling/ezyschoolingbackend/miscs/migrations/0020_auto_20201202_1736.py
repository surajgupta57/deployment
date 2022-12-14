# Generated by Django 2.2.16 on 2020-12-02 12:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0024_auto_20201104_0743'),
        ('miscs', '0019_talenthuntsubmission_referrer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='talenthuntsubmission',
            name='referrer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referrals', to='miscs.TalentHuntSubmission'),
        ),
        migrations.CreateModel(
            name='AdmissionAlert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('email', models.EmailField(max_length=254)),
                ('phone_no', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('region', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.Region')),
            ],
            options={
                'verbose_name': 'Admission Alert',
                'verbose_name_plural': 'Admission Alerts',
            },
        ),
    ]
