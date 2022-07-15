from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0050_studentgroupassignment_show_correct_answers'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='favourite_questions',
            field=models.ManyToManyField(related_name='favourite_questions', to='peerinst.Question', blank=True),
        ),
    ]
