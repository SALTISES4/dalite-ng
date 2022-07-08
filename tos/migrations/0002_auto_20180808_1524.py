from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tos', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='emailconsent',
            options={'get_latest_by': 'datetime'},
        ),
    ]
