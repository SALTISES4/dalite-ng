import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0048_auto_20180808_2100'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentgroupassignment',
            name='distribution_date',
            field=models.DateTimeField(default=datetime.datetime(2018, 8, 9, 3, 5, 12, 811108, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
