from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0051_teacher_favourite_questions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='text',
            field=models.TextField(help_text='Enter the question text.', verbose_name='Question text'),
        ),
        migrations.AlterField(
            model_name='question',
            name='title',
            field=models.CharField(help_text='A title for the question.', unique=True, max_length=100, verbose_name='Question title'),
        ),
    ]
