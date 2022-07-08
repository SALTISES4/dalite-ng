from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0055_group_copy'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentgroup',
            name='student_id_needed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentgroupmembership',
            name='student_school_id',
            field=models.TextField(null=True, blank=True),
        ),
    ]
