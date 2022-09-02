# Generated by Django 2.2.10 on 2021-01-28 06:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0033_merge_20210122_1728'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='admmissionopenclasses',
            options={'ordering': ['class_relation__rank'], 'verbose_name': 'School Admission Open Classes', 'verbose_name_plural': 'School Admission Open Classes'},
        ),
        migrations.AlterModelOptions(
            name='schoolview',
            options={'ordering': ('-updated_at', 'id'), 'verbose_name': 'School View', 'verbose_name_plural': 'School Views'},
        ),
        migrations.AddField(
            model_name='schoolprofile',
            name='hide_point_calculator',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='distancepoint',
            name='school',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='distance_points', to='schools.SchoolProfile'),
        ),
        migrations.AlterField(
            model_name='schoolprofile',
            name='point_system',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='AgeCriteria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('class_relation', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='schools.SchoolClasses')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='schools.SchoolProfile')),
            ],
            options={
                'verbose_name': 'Age Criteria',
                'verbose_name_plural': 'Age Criteria',
            },
        ),
    ]
