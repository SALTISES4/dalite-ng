from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0040_auto_20180720_1519'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='deleted_questions',
            field=models.ManyToManyField(to='peerinst.Question', blank=True),
        ),
    ]
