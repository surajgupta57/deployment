# Generated by Django 2.2.10 on 2020-04-04 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0002_auto_20200331_1738'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admmissionopenclasses',
            name='draft',
            field=models.BooleanField(default=False),
        ),
    ]
