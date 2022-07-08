from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0039_auto_20180718_2348'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentgroup',
            name='creation_date',
            field=models.DateField(auto_now=True, null=True),
        ),
    ]
