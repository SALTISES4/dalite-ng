from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0011_auto_20180129_1922'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='category',
            field=models.ManyToManyField(to='peerinst.Category', blank=True),
        ),
    ]
