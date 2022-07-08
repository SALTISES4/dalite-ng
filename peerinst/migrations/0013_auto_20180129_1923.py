from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0012_auto_20180129_1923'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacher',
            name='assignments',
            field=models.ManyToManyField(to='peerinst.Assignment', blank=True),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='disciplines',
            field=models.ManyToManyField(to='peerinst.Discipline', blank=True),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='groups',
            field=models.ManyToManyField(to='peerinst.Group', blank=True),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='institutions',
            field=models.ManyToManyField(to='peerinst.Institution', blank=True),
        ),
    ]
