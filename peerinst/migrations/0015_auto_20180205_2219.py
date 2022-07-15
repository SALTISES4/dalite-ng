from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0014_auto_20180129_2002'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='studentgroup',
            options={'ordering': ['-creation_date'], 'verbose_name': 'group', 'verbose_name_plural': 'groups'},
        ),
        migrations.AddField(
            model_name='studentgroup',
            name='creation_date',
            field=models.DateField(null=True, blank=True),
        ),
    ]
