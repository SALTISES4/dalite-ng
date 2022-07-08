from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0056_auto_20181123_1451'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentnotification',
            name='expiration',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
