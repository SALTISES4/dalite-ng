import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("peerinst", "0015_auto_20180205_2219"),
    ]

    operations = [
        migrations.CreateModel(
            name="BlinkAnswer",
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
                    "answer_choice",
                    models.PositiveSmallIntegerField(
                        verbose_name="Answer choice"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="BlinkQuestion",
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
                ("key", models.CharField(unique=True, max_length=8)),
                (
                    "question",
                    models.ForeignKey(
                        to="peerinst.Question",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="blinkanswer",
            name="question",
            field=models.ForeignKey(
                to="peerinst.BlinkQuestion",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
