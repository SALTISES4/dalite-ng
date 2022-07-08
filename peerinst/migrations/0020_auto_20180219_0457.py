from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0019_auto_20180219_0448'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='blinkanswer',
            name='question',
        ),
        migrations.RemoveField(
            model_name='blinkquestion',
            name='id',
        ),
        migrations.AlterField(
            model_name='blinkquestion',
            name='key',
            field=models.CharField(max_length=8, unique=True, serialize=False, primary_key=True),
        ),
    ]
