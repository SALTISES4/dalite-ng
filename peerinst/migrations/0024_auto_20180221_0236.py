from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0023_auto_20180221_0216'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blinkround',
            name='activate_time',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='blinkround',
            name='deactivate_time',
            field=models.DateTimeField(null=True),
        ),
    ]
