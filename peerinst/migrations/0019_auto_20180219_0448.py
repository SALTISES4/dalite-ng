from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0018_blinkquestion_activate_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blinkquestion',
            name='activate_time',
            field=models.DateTimeField(),
        ),
    ]
