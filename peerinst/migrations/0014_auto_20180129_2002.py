from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0013_auto_20180129_1923'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Group',
            new_name='StudentGroup',
        ),
        migrations.AlterField(
            model_name='institution',
            name='name',
            field=models.CharField(help_text='Name of school.', unique=True, max_length=100),
        ),
    ]
