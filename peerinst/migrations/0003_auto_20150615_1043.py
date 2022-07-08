from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0002_auto_20150430_2108'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='expert',
            field=models.BooleanField(default=False, help_text='Whether this answer is a pre-seeded expert rationale.', verbose_name='Expert rationale?'),
        ),
        migrations.AddField(
            model_name='question',
            name='rationale_selection_algorithm',
            field=models.CharField(default='prefer_expert_and_highly_voted', help_text='The algorithm to use for choosing the rationales presented to students during question review.', max_length=100, verbose_name='Rationale selection algorithm', choices=[('simple', 'Simple random rationale selection'), ('prefer_expert_and_highly_voted', 'Prefer expert and highly votes rationales')]),
        ),
    ]
