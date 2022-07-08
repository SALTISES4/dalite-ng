from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0001_squashed_0012_auto_20150423_1146'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='show_to_others',
            field=models.BooleanField(default=True, verbose_name='Show to others?'),
        ),
    ]
