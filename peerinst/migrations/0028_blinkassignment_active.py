from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0027_auto_20180227_2142'),
    ]

    operations = [
        migrations.AddField(
            model_name='blinkassignment',
            name='active',
            field=models.BooleanField(default=False),
        ),
    ]
