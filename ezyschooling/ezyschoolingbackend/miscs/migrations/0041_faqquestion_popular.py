# Generated by Django 2.2.10 on 2021-09-28 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('miscs', '0040_faqquestion_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='faqquestion',
            name='popular',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]