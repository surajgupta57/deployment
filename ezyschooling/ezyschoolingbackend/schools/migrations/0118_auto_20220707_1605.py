# Generated by Django 2.2.10 on 2022-07-07 10:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0117_auto_20220706_1257'),
    ]

    operations = [
        migrations.AddField(
            model_name='schooleqnuirysource',
            name='campaign_name',
            field=models.CharField(blank=True, max_length=80, null=True),
        ),
        migrations.AddField(
            model_name='schoolprofile',
            name='ad_source',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
