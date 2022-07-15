from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0010_auto_20180129_1920'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='category',
        ),
        migrations.AddField(
            model_name='question',
            name='category',
            field=models.ManyToManyField(to='peerinst.Category', null=True, blank=True),
        ),
    ]
