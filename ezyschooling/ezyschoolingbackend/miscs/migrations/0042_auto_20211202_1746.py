# Generated by Django 2.2.10 on 2021-12-02 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('miscs', '0041_faqquestion_popular'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admissionguidance',
            name='target_region',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
