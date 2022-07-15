import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0021_blinkanswer_question'),
    ]

    operations = [
        migrations.AddField(
            model_name='blinkanswer',
            name='vote_time',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 20, 3, 8, 26, 393523, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='blinkquestion',
            name='deactivate_time',
            field=models.DateTimeField(default=datetime.datetime(2018, 2, 20, 3, 8, 37, 533009, tzinfo=utc), blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='teacher',
            name='blinks',
            field=models.ManyToManyField(to='peerinst.BlinkQuestion', blank=True),
        ),
        migrations.AlterField(
            model_name='blinkquestion',
            name='activate_time',
            field=models.DateTimeField(blank=True),
        ),
    ]
