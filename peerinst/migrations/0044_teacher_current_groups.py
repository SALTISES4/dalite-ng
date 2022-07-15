from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0043_auto_20180803_0135'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='current_groups',
            field=models.ManyToManyField(related_name='current_groups', to='peerinst.StudentGroup', blank=True),
        ),
    ]
