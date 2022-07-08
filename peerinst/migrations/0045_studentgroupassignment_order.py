from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0044_teacher_current_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentgroupassignment',
            name='order',
            field=models.TextField(editable=False, blank=True),
        ),
    ]
