from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0008_question_grading_scheme'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='answerchoice',
            options={'ordering': ['id'], 'verbose_name': 'answer choice', 'verbose_name_plural': 'answer choices'},
        ),
    ]
