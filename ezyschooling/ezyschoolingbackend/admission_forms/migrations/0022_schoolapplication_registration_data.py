# Generated by Django 2.2.10 on 2021-06-30 08:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('admission_forms', '0021_auto_20210630_1124'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolapplication',
            name='registration_data',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='common_reg_form_after_payment', to='admission_forms.CommonRegistrationFormAfterPayment'),
        ),
    ]