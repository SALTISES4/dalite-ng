# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-24 16:56
from __future__ import unicode_literals

from django.db import migrations, models
import quality.models.custom_fields


class Migration(migrations.Migration):

    dependencies = [
        ("quality", "0006_likelihoodcriterion_likelihoodcriterionrules")
    ]

    operations = [
        migrations.CreateModel(
            name="LikelihoodLanguage",
            fields=[
                (
                    "language",
                    models.CharField(
                        max_length=32, primary_key=True, serialize=False
                    ),
                ),
                ("left_to_right", models.BooleanField(default=True)),
                ("n_gram_urls", quality.models.custom_fields.CommaSepField()),
            ],
        ),
        migrations.RemoveField(
            model_name="likelihoodcriterionrules", name="languages"
        ),
        migrations.AddField(
            model_name="likelihoodcriterionrules",
            name="languages",
            field=models.ManyToManyField(
                help_text="Accepted languages.",
                to="quality.LikelihoodLanguage",
                verbose_name="Languages",
            ),
        ),
    ]