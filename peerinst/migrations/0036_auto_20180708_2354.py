import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import peerinst.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("peerinst", "0035_auto_20180527_2123"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="collaborators",
            field=models.ManyToManyField(
                help_text="Optional. Other users that may also edit this question.",
                related_name="collaborators",
                to=settings.AUTH_USER_MODEL,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="question",
            name="created_on",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="question",
            name="last_modified",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name="question",
            name="user",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                blank=True,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="discipline",
            name="title",
            field=models.CharField(
                help_text="Name of a discipline.",
                unique=True,
                max_length=100,
                verbose_name="Discipline name",
                validators=[peerinst.models.no_hyphens],
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="category",
            field=models.ManyToManyField(
                help_text="Optional. Select categories for this question.  You can select multiple categories.",
                db_constraint="Categories",
                to="peerinst.Category",
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="discipline",
            field=models.ForeignKey(
                blank=True,
                to="peerinst.Discipline",
                help_text="Optional. Select the discipline to which this question should be associated.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="image",
            field=models.ImageField(
                help_text="Optional. An image to include after the question text.",
                upload_to="images",
                null=True,
                verbose_name="Question image",
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="image_alt_text",
            field=models.CharField(
                help_text="Optional. Alternative text for accessibility. For instance, the student may be using a screen reader.",
                max_length=1024,
                verbose_name="Image Alt Text",
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="video_url",
            field=models.URLField(
                help_text="Optional. A video to include after the question text. All videos should include transcripts.",
                verbose_name="Question video URL",
                blank=True,
            ),
        ),
    ]
