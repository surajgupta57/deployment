# Generated by Django 2.2.10 on 2021-04-29 08:59

from django.db import migrations, models
import miscs.utils


class Migration(migrations.Migration):

    dependencies = [
        ('miscs', '0027_invitedprincipals_pastandcurrentimpactinars_sponsorsregistrations_webinarregistrations'),
    ]

    operations = [
        migrations.CreateModel(
            name='Testimonials',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('message', models.TextField(blank=True, null=True)),
                ('designation', models.CharField(blank=True, max_length=255, null=True)),
                ('photo', models.FileField(blank=True, null=True, upload_to=miscs.utils.user_testimonial_upload_path)),
                ('is_school', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'User Testimonial',
                'verbose_name_plural': 'User Testimonials',
            },
        ),
        migrations.AlterModelOptions(
            name='invitedprincipals',
            options={'verbose_name': 'Invited Principal', 'verbose_name_plural': 'Invited Principals'},
        ),
    ]
