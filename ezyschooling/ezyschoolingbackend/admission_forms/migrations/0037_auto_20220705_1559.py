# Generated by Django 2.2.10 on 2022-07-05 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admission_forms', '0036_auto_20220608_1652'),
    ]

    operations = [
        migrations.AddField(
            model_name='childschoolcart',
            name='ad_source',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='schoolapplication',
            name='ad_source',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
