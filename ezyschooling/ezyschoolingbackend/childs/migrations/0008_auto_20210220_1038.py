# Generated by Django 2.2.10 on 2021-02-20 05:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('childs', '0007_auto_20210219_1407'),
    ]

    operations = [
        migrations.AlterField(
            model_name='child',
            name='blood_group',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]
