# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-03-27 14:07
from __future__ import unicode_literals

from django.db import migrations
import quality.models.custom_fields


class Migration(migrations.Migration):

    dependencies = [("quality", "0002_auto_20190326_2040")]

    operations = [
        migrations.AlterField(
            model_name="mincharscriterion",
            name="uses_rules",
            field=quality.models.custom_fields.CommaSepField(
                blank=True,
                help_text="Comma separated list of used rules for the criterion found as the fields of the associated rules object. Make sure to use the verbose_name",
            ),
        ),
        migrations.AlterField(
            model_name="minwordscriterion",
            name="uses_rules",
            field=quality.models.custom_fields.CommaSepField(
                blank=True,
                help_text="Comma separated list of used rules for the criterion found as the fields of the associated rules object. Make sure to use the verbose_name",
            ),
        ),
        migrations.AlterField(
            model_name="negwordscriterion",
            name="uses_rules",
            field=quality.models.custom_fields.CommaSepField(
                blank=True,
                help_text="Comma separated list of used rules for the criterion found as the fields of the associated rules object. Make sure to use the verbose_name",
            ),
        ),
    ]