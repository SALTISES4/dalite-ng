import re

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0052_auto_20180924_1420'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='identifier',
            field=models.CharField(primary_key=True, serialize=False, max_length=100, validators=[django.core.validators.RegexValidator(re.compile('^[-a-zA-Z0-9_]+\\Z'), "Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens.", 'invalid')], help_text='A unique identifier for this assignment used for inclusion in a course.', verbose_name='identifier'),
        ),
    ]
