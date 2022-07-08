import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("peerinst", "0042_merge"),
    ]

    operations = [
        migrations.CreateModel(
            name="StudentAssignment",
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
                ("first_access", models.DateTimeField(auto_now=True)),
                ("last_access", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="StudentGroupAssignment",
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
                ("due_date", models.DateTimeField(null=True, blank=True)),
                (
                    "assignment",
                    models.ForeignKey(
                        to="peerinst.Assignment",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.RemoveField(model_name="teacher", name="groups",),
        migrations.AddField(
            model_name="studentgroup",
            name="teacher",
            field=models.ManyToManyField(to="peerinst.Teacher", blank=True),
        ),
        migrations.AlterField(
            model_name="answer",
            name="user_token",
            field=models.CharField(
                help_text="Corresponds to the user's username.",
                max_length=100,
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="fake_attributions",
            field=models.BooleanField(
                default=False,
                help_text="Add random fake attributions consisting of username and country to rationales. You can configure the lists of fake values and countries from the start page of the admin interface.",
                verbose_name="Add fake attributions",
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="image",
            field=models.ImageField(
                help_text="Optional. An image to include after the question text. Accepted formats: .jpg, .jpeg, .png, .gif",
                upload_to="images",
                null=True,
                verbose_name="Question image",
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="question",
            name="text",
            field=models.TextField(
                help_text='Enter the question text.  You can use HTML tags for formatting. You can use the "Preview" button in the top right corner to see what the question will look like for students.  The button appears after saving the question for the first time.',
                verbose_name="Question text",
            ),
        ),
        migrations.AddField(
            model_name="studentgroupassignment",
            name="group",
            field=models.ForeignKey(
                to="peerinst.StudentGroup",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="studentassignment",
            name="group_assignment",
            field=models.ForeignKey(
                to="peerinst.StudentGroupAssignment",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="studentassignment",
            name="student",
            field=models.ForeignKey(
                to="peerinst.Student",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="studentassignment",
            unique_together={("student", "group_assignment")},
        ),
    ]
