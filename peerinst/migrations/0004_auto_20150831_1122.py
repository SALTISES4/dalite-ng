from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0003_auto_20150615_1043'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='downvotes',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='answer',
            name='upvotes',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='question',
            name='sequential_review',
            field=models.BooleanField(default=False, help_text='Show rationales sequentially and allow to vote on them before the final review.', verbose_name='Sequential rationale review'),
        ),
    ]
