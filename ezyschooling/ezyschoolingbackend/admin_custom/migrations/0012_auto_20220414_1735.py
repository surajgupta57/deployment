# Generated by Django 2.2.10 on 2022-04-14 12:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('admin_custom', '0011_auto_20220414_1728'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='schoolaction',
            options={'verbose_name': 'Action Performed by School', 'verbose_name_plural': 'Actions Performed by School'},
        ),
        migrations.AddField(
            model_name='schoolaction',
            name='parent_action',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='counselling_action_relation_a', to='admin_custom.CounselingAction', verbose_name="Counsellor's Action(A)"),
        ),
    ]