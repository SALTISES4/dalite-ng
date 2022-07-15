from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0028_blinkassignment_active'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blinkassignment',
            options={'verbose_name': 'blink assignment', 'verbose_name_plural': 'blink assignments'},
        ),
        migrations.RemoveField(
            model_name='teacher',
            name='blinkassignments',
        ),
        migrations.RemoveField(
            model_name='teacher',
            name='blinks',
        ),
    ]
