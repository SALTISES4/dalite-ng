# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-16 17:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "quality",
            "0005_selectedanswercriterion_selectedanswercriterionrules",
        )
    ]

    operations = [
        migrations.AddField(
            model_name="qualitytype",
            name="model",
            field=models.CharField(blank=True, max_length=32, null=True),
        )
    ]
