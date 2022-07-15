from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0007_answervote'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='grading_scheme',
            field=models.IntegerField(default=0, help_text='Grading scheme to use. The "Standard" scheme awards 1 point if the student\'s final answer is correct, and 0 points otherwise. The "Advanced" scheme awards 0.5 points if the student\'s initial guess is correct, and 0.5 points if they subsequently stick with or change to the correct answer.', verbose_name='Grading scheme', choices=[(0, 'Standard'), (1, 'Advanced')]),
        ),
    ]
