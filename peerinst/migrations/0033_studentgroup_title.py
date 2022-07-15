from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0032_verifieddomain'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentgroup',
            name='title',
            field=models.CharField(default=None, max_length=100),
        ),
    ]
