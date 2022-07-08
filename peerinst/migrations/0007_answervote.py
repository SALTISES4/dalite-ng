import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("peerinst", "0006_question_fake_attributions"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnswerVote",
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
                ("user_token", models.CharField(max_length=100)),
                ("fake_username", models.CharField(max_length=100)),
                ("fake_country", models.CharField(max_length=100)),
                (
                    "vote_type",
                    models.PositiveSmallIntegerField(
                        verbose_name="Vote type",
                        choices=[
                            (0, "upvote"),
                            (1, "downvote"),
                            (2, "final_choice"),
                        ],
                    ),
                ),
                (
                    "answer",
                    models.ForeignKey(
                        to="peerinst.Answer",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "assignment",
                    models.ForeignKey(
                        to="peerinst.Assignment",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
        ),
    ]
