# Generated by Django 2.2.10 on 2021-11-29 10:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0077_auto_20211129_1519'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videotourlinks',
            name='link',
            field=models.TextField(blank=True, help_text='Seprate multiple links using comma(,) . Also do not use space in between the links', null=True, verbose_name='Links'),
        ),
        # migrations.AlterUniqueTogether(
        #     name='agecriteria',
        #     unique_together={('school', 'class_relation', 'session')},
        # ),
    ]