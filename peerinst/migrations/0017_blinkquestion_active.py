from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0016_auto_20180216_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='blinkquestion',
            name='active',
            field=models.BooleanField(default=False),
        ),
    ]
