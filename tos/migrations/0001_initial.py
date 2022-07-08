import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Consent",
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
                ("accepted", models.BooleanField()),
                ("datetime", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="EmailConsent",
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
                ("accepted", models.BooleanField()),
                ("datetime", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="EmailType",
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
                ("type", models.CharField(max_length=32)),
                ("title", models.TextField()),
                ("description", models.TextField()),
                ("show_order", models.PositiveIntegerField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                (
                    "role",
                    models.CharField(
                        max_length=32, serialize=False, primary_key=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Tos",
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
                ("version", models.PositiveIntegerField()),
                ("hash", models.CharField(max_length=32, editable=False)),
                ("text", models.TextField()),
                ("created", models.DateTimeField(auto_now=True)),
                ("current", models.BooleanField()),
                (
                    "role",
                    models.ForeignKey(
                        to="tos.Role",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="emailtype",
            name="role",
            field=models.ForeignKey(
                to="tos.Role", on_delete=django.db.models.deletion.CASCADE
            ),
        ),
        migrations.AddField(
            model_name="emailconsent",
            name="email_type",
            field=models.ForeignKey(
                to="tos.EmailType", on_delete=django.db.models.deletion.CASCADE
            ),
        ),
        migrations.AddField(
            model_name="emailconsent",
            name="user",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="consent",
            name="tos",
            field=models.ForeignKey(
                to="tos.Tos", on_delete=django.db.models.deletion.CASCADE
            ),
        ),
        migrations.AddField(
            model_name="consent",
            name="user",
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="tos",
            unique_together={("role", "hash"), ("role", "version")},
        ),
        migrations.AlterUniqueTogether(
            name="emailtype", unique_together={("role", "type")},
        ),
    ]
