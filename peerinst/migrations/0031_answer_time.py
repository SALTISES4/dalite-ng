from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0030_auto_20180324_0320'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='time',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
