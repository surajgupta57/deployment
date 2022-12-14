# Generated by Django 2.2.10 on 2021-04-05 13:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parents', '0013_parentaddress_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parentaddress',
            name='user',
            field=models.ForeignKey(blank=True, limit_choices_to={'is_parent': True}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parent_address_user', to=settings.AUTH_USER_MODEL),
        ),
    ]
