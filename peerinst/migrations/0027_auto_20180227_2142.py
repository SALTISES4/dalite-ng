import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("peerinst", "0026_blinkquestion_current"),
    ]

    operations = [
        migrations.CreateModel(
            name="BlinkAssignment",
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
                    models.CharField(max_length=200, verbose_name="Title"),
                ),
                ("key", models.CharField(unique=True, max_length=8)),
            ],
            options={
                "verbose_name": "blinkassignment",
                "verbose_name_plural": "blinkassignments",
            },
        ),
        migrations.CreateModel(
            name="BlinkAssignmentQuestion",
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
                ("rank", models.IntegerField()),
                (
                    "blinkassignment",
                    models.ForeignKey(
                        to="peerinst.BlinkAssignment",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "blinkquestion",
                    models.ForeignKey(
                        to="peerinst.BlinkQuestion",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={"ordering": ["rank"],},
        ),
        migrations.AddField(
            model_name="blinkassignment",
            name="blinkquestions",
            field=models.ManyToManyField(
                to="peerinst.BlinkQuestion",
                through="peerinst.BlinkAssignmentQuestion",
            ),
        ),
        migrations.AddField(
            model_name="teacher",
            name="blinkassignments",
            field=models.ManyToManyField(
                to="peerinst.BlinkAssignment", blank=True
            ),
        ),
    ]
