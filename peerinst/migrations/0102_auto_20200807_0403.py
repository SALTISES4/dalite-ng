# Generated by Django 2.2.14 on 2020-08-07 04:03

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import peerinst.models.group


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0102_auto_20200807_0346'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentgroup',
            name='discipline',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='peerinst.Discipline'),
        ),
        migrations.AddField(
            model_name='studentgroup',
            name='semester',
            field=models.CharField(choices=[('FALL', 'Fall'), ('SUMMER', 'Summer'), ('WINTER', 'Winter')], default='FALL', max_length=6),
        ),
        migrations.AddField(
            model_name='studentgroup',
            name='year',
            field=models.PositiveIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), peerinst.models.group.max_value_current_year]),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='conclusion_page',
            field=models.TextField(blank=True, help_text='Any notes you would like to leave for students\n            to read that will be shown after the last\n            question of the assignment.\n            ', null=True, verbose_name='Post Assignment Notes'),
        ),
    ]
