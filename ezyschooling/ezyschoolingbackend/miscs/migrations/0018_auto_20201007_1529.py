# Generated by Django 2.2.10 on 2020-10-07 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('miscs', '0017_faqcategory_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admissionguidance',
            name='dob',
            field=models.DateField(blank=True, null=True, verbose_name="Child's Date of Birth"),
        ),
    ]