import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0017_blinkquestion_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='blinkquestion',
            name='activate_time',
            field=models.TimeField(default=datetime.datetime(2018, 2, 19, 4, 29, 25, 31840, tzinfo=utc)),
            preserve_default=False,
        ),
    ]
