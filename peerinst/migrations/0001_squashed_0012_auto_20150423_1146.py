import django.db.models.deletion
from django.db import migrations, models

import peerinst.models


class Migration(migrations.Migration):

    replaces = [
        ("peerinst", "0001_initial"),
        ("peerinst", "0002_auto_20150410_1137"),
        ("peerinst", "0003_question_text"),
        ("peerinst", "0004_answer"),
        ("peerinst", "0005_auto_20150410_1422"),
        ("peerinst", "0006_auto_20150410_1809"),
        ("peerinst", "0007_auto_20150416_1136"),
        ("peerinst", "0008_auto_20150416_1142"),
        ("peerinst", "0009_auto_20150420_2008"),
        ("peerinst", "0009_auto_20150416_2103"),
        ("peerinst", "0009_answer_assignment"),
        ("peerinst", "0010_merge"),
        ("peerinst", "0011_auto_20150422_0006"),
        ("peerinst", "0012_auto_20150423_1146"),
    ]

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AnswerChoice",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "text",
                    models.CharField(max_length=500, verbose_name="Text"),
                ),
                ("correct", models.BooleanField(verbose_name="Correct?")),
            ],
            options={
                "verbose_name": "answer choice",
                "verbose_name_plural": "answer choices",
            },
        ),
        migrations.CreateModel(
            name="Assignment",
            fields=[
                (
                    "identifier",
                    models.CharField(
                        help_text="A unique identifier for this assignment used for inclusion in a course.",
                        max_length=100,
                        serialize=False,
                        verbose_name="identifier",
                        primary_key=True,
                    ),
                ),
                (
                    "title",
                    models.CharField(max_length=200, verbose_name="Title"),
                ),
            ],
            options={
                "verbose_name": "assignment",
                "verbose_name_plural": "assignments",
            },
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        help_text="The question name must follow the conventions of course name abreviation plus question and number: LynDynQ14.",
                        unique=True,
                        max_length=100,
                        verbose_name="Question title",
                    ),
                ),
                (
                    "primary_image",
                    models.ImageField(
                        help_text="An image to include on the first page of the question.",
                        upload_to="images",
                        null=True,
                        verbose_name="Main question image",
                        blank=True,
                    ),
                ),
                (
                    "primary_video_url",
                    models.URLField(
                        help_text="A video to include on the first page of the question.",
                        verbose_name="Main question video URL",
                        blank=True,
                    ),
                ),
                (
                    "secondary_image",
                    models.ImageField(
                        upload_to="images",
                        null=True,
                        verbose_name="Secondary question image",
                        blank=True,
                    ),
                ),
                (
                    "secondary_video_url",
                    models.URLField(
                        verbose_name="Secondary question video URL", blank=True
                    ),
                ),
                (
                    "answer_style",
                    models.IntegerField(
                        default=0,
                        help_text="Whether the answers are annotated with letters (A, B, C\u2026) or numbers (1, 2, 3\u2026).",
                        verbose_name="Answer style",
                        choices=[(0, "alphabetic"), (1, "numeric")],
                    ),
                ),
                (
                    "example_rationale",
                    models.TextField(
                        help_text="An example of a good rationale for the question.",
                        verbose_name="Example for a good rationale",
                    ),
                ),
                (
                    "example_answer",
                    models.PositiveSmallIntegerField(
                        help_text="The answer associated with the example rationale (1=first, 2=second, etc.).",
                        verbose_name="Example answer",
                    ),
                ),
                (
                    "text",
                    models.TextField(
                        default="text",
                        help_text="Enter the question text.  You can use HTML tags for formatting.",
                        verbose_name="Question text",
                    ),
                ),
            ],
            options={
                "verbose_name": "question",
                "verbose_name_plural": "questions",
            },
        ),
        migrations.CreateModel(
            name='AssignmentQuestions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'peerinst_assignment_questions',
            },
        ),
        migrations.AddField(
            model_name='assignment',
            name='questions',
            field=models.ManyToManyField(through='peerinst.AssignmentQuestions', to='peerinst.Question', verbose_name='Questions'),
        ),
        migrations.AddField(
            model_name='assignmentquestions',
            name='assignment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='peerinst.Assignment'),
        ),
        migrations.AddField(
            model_name='assignmentquestions',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='peerinst.Question'),
        ),
        migrations.AlterUniqueTogether(
            name='assignmentquestions',
            unique_together={('assignment', 'question')},
        ),
        migrations.AddField(
            model_name="answerchoice",
            name="question",
            field=models.ForeignKey(
                to="peerinst.Question",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.CreateModel(
            name="Answer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "first_answer_choice",
                    models.PositiveSmallIntegerField(
                        verbose_name="First answer choice"
                    ),
                ),
                ("rationale", models.TextField(verbose_name="Rationale")),
                (
                    "second_answer_choice",
                    models.PositiveSmallIntegerField(
                        null=True,
                        verbose_name="Second answer choice",
                        blank=True,
                    ),
                ),
                ("user_token", models.CharField(max_length=100, blank=True)),
                (
                    "show_to_others",
                    models.BooleanField(
                        default=False, verbose_name="Show to others?"
                    ),
                ),
                (
                    "chosen_rationale",
                    models.ForeignKey(
                        blank=True,
                        to="peerinst.Answer",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "question",
                    models.ForeignKey(
                        to="peerinst.Question",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "assignment",
                    models.ForeignKey(
                        blank=True,
                        to="peerinst.Assignment",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.RemoveField(model_name="question", name="example_answer",),
        migrations.RemoveField(
            model_name="question", name="example_rationale",
        ),
        migrations.RemoveField(model_name="question", name="secondary_image",),
        migrations.RemoveField(
            model_name="question", name="secondary_video_url",
        ),
        migrations.RemoveField(model_name="question", name="primary_image",),
        migrations.RemoveField(
            model_name="question", name="primary_video_url",
        ),
        migrations.AddField(
            model_name="question",
            name="image",
            field=models.ImageField(
                help_text="An image to include after the question text.",
                upload_to="images",
                null=True,
                verbose_name="Question image",
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="question",
            name="video_url",
            field=models.URLField(
                help_text="A video to include after the question text. All videos should include transcripts.",
                verbose_name="Question video URL",
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="question",
            name="image_alt_text",
            field=models.CharField(
                help_text="Alternative text for accessibility. For instance, the student may be using a screen reader.",
                max_length=1024,
                verbose_name="Image Alt Text",
                blank=True,
            ),
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        help_text="Name of a category questions can be sorted into.",
                        unique=True,
                        max_length=100,
                        verbose_name="Category Name",
                        validators=[peerinst.models.no_hyphens],
                    ),
                ),
            ],
            options={
                "verbose_name": "category",
                "verbose_name_plural": "categories",
            },
        ),
        migrations.AddField(
            model_name="question",
            name="category",
            field=models.ForeignKey(
                blank=True,
                to="peerinst.Category",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="id",
            field=models.AutoField(
                help_text="Use this ID to refer to the question in the LMS. Note: The question will have to have been saved at least once before an ID is available.",
                serialize=False,
                primary_key=True,
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="title",
            field=models.CharField(
                help_text="A title for the question. Presented to the user, and used for lookup when creating assignments.",
                unique=True,
                max_length=100,
                verbose_name="Question title",
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="text",
            field=models.TextField(
                help_text='Enter the question text.  You can use HTML tags for formatting.  You can use the "Preview" button in the top right corner to see what the question will look like for students.  The button appears after saving the question for the first time.',
                verbose_name="Question text",
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="title",
            field=models.CharField(
                help_text="A title for the question. Used for lookup when creating assignments, but not presented to the student.",
                unique=True,
                max_length=100,
                verbose_name="Question title",
            ),
        ),
    ]
