from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0034_assignment_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentgroup',
            name='title',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
