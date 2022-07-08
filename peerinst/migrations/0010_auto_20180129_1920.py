import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import peerinst.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("peerinst", "0009_auto_20160210_2236"),
    ]

    operations = [
        migrations.CreateModel(
            name="Discipline",
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
                        help_text="Name of a discipline.",
                        unique=True,
                        max_length=100,
                        verbose_name="Discipline Name",
                        validators=[peerinst.models.no_hyphens],
                    ),
                ),
            ],
            options={
                "verbose_name": "discipline",
                "verbose_name_plural": "disciplines",
            },
        ),
        migrations.CreateModel(
            name="Group",
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
                ("name", models.CharField(unique=True, max_length=100)),
            ],
            options={
                "verbose_name": "group",
                "verbose_name_plural": "groups",
            },
        ),
        migrations.CreateModel(
            name="Institution",
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
                ("name", models.CharField(unique=True, max_length=100)),
            ],
            options={
                "verbose_name": "institution",
                "verbose_name_plural": "institutions",
            },
        ),
        migrations.CreateModel(
            name="Student",
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
                    "groups",
                    models.ManyToManyField(to="peerinst.Group", blank=True),
                ),
                (
                    "student",
                    models.OneToOneField(
                        to=settings.AUTH_USER_MODEL,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "student",
                "verbose_name_plural": "students",
            },
        ),
        migrations.CreateModel(
            name="Teacher",
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
                    "assignments",
                    models.ManyToManyField(to="peerinst.Assignment"),
                ),
                (
                    "disciplines",
                    models.ManyToManyField(to="peerinst.Discipline"),
                ),
                ("groups", models.ManyToManyField(to="peerinst.Group")),
                (
                    "institutions",
                    models.ManyToManyField(to="peerinst.Institution"),
                ),
                (
                    "user",
                    models.OneToOneField(
                        to=settings.AUTH_USER_MODEL,
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={
                "verbose_name": "teacher",
                "verbose_name_plural": "teachers",
            },
        ),
        migrations.AddField(
            model_name="question",
            name="discipline",
            field=models.ForeignKey(
                blank=True,
                to="peerinst.Discipline",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
