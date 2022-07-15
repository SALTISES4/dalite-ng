from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0055_group_copy'),
    ]

    operations = [
        migrations.CreateModel(
            name='RationaleOnlyQuestion',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('peerinst.question',),
        ),
        migrations.AddField(
            model_name='question',
            name='type',
            field=models.CharField(default='PI', help_text="Choose 'peer instruction' for two-step multiple choice with rationale or 'rationale only' for a simple text response.", max_length=2, verbose_name='Question type', choices=[('PI', 'Peer instruction'), ('RO', 'Rationale only')]),
        ),
        migrations.AlterField(
            model_name='question',
            name='video_url',
            field=models.URLField(help_text='Optional. A video to include after the question text. All videos should include transcripts.  Format: https://www.youtube.com/embed/...', verbose_name='Question video URL', blank=True),
        ),
    ]
