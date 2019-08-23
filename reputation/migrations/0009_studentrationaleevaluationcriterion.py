# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-08-23 15:30
from __future__ import unicode_literals

import dalite.models.custom_fields
from django.db import migrations, models
import reputation.models.criteria.criterion


class Migration(migrations.Migration):

    dependencies = [
        ('reputation', '0008_commonrationalechoicescriterion'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentRationaleEvaluationCriterion',
            fields=[
                ('version', models.AutoField(primary_key=True, serialize=False)),
                ('badge_thresholds', dalite.models.custom_fields.CommaSepField(blank=True, help_text='Thresholds for the badges to be awarded.', validators=[reputation.models.criteria.criterion.validate_list_floats_greater_0])),
                ('badge_colour', models.CharField(default='#0066ff', max_length=16)),
                ('points_per_threshold', dalite.models.custom_fields.CommaSepField(help_text='Number of reputation points for each criterion point up to the next threadhold, split by commas. This list should have the same length or have one more element than Thresholds.', verbose_name='Points per threshold')),
                ('thresholds', dalite.models.custom_fields.CommaSepField(blank=True, default='', help_text="Thresholds for number of point change. If empty, all criterion points will give the same number of points. If one less than `Points per threshold`, the last point number goes to infinity. If it's the same length, the last number indicates the threshold after which points aren't gained.", verbose_name='Thresholds')),
                ('name', models.CharField(default='student_rationale_evaluation', editable=False, max_length=32)),
                ('for_reputation_types', models.ManyToManyField(to='reputation.ReputationType')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
