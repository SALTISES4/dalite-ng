from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0049_studentgroupassignment_distribution_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentgroupassignment',
            name='show_correct_answers',
            field=models.BooleanField(default=True, help_text='Check if students should be shown correct answer after completing the question.', verbose_name='Show correct answers'),
        ),
    ]
