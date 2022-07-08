import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0046_auto_20180808_1524'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentgroupassignment',
            name='due_date',
            field=models.DateTimeField(default=datetime.datetime.utcnow),
        ),
    ]
