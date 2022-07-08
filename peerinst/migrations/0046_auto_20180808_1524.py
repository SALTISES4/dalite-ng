import datetime

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0045_studentgroupassignment_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentgroupassignment',
            name='due_date',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]
