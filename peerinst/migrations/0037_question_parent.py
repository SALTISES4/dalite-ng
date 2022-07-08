import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0036_auto_20180708_2354'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='peerinst.Question', null=True),
        ),
    ]
