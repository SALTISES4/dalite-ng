import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("peerinst", "0053_auto_20181023_0341"),
    ]

    operations = [
        migrations.CreateModel(
            name="StudentGroupMembership",
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
                ("current_member", models.BooleanField(default=True)),
                ("send_emails", models.BooleanField(default=True)),
                (
                    "group",
                    models.ForeignKey(
                        to="peerinst.StudentGroup",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StudentNotification",
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
                ("created_on", models.DateTimeField(auto_now=True, null=True)),
                (
                    "link",
                    models.URLField(max_length=500, null=True, blank=True),
                ),
                ("text", models.TextField()),
                ("hover_text", models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="StudentNotificationType",
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
                ("type", models.CharField(unique=True, max_length=32)),
                ("icon", models.TextField()),
            ],
        ),
        migrations.AlterModelOptions(name="verifieddomain", options={},),
        migrations.AddField(
            model_name="student",
            name="send_reminder_email_day_before",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="student",
            name="send_reminder_email_every_day",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="studentassignment",
            name="reminder_sent",
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name="studentgroupassignment",
            name="reminder_days",
            field=models.PositiveIntegerField(default=3),
        ),
        migrations.AlterField(
            model_name="verifieddomain",
            name="domain",
            field=models.CharField(
                help_text="Teacher-only email domain, if available. Email addresses with these domains will be treated as verified.",
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name="studentnotification",
            name="notification",
            field=models.ForeignKey(
                to="peerinst.StudentNotificationType",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="studentnotification",
            name="student",
            field=models.ForeignKey(
                to="peerinst.Student",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="studentgroupmembership",
            name="student",
            field=models.ForeignKey(
                to="peerinst.Student",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="student",
            name="student_groups",
            field=models.ManyToManyField(
                related_name="groups_new",
                through="peerinst.StudentGroupMembership",
                to="peerinst.StudentGroup",
                blank=True,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="studentgroupmembership",
            unique_together={("student", "group")},
        ),
    ]
