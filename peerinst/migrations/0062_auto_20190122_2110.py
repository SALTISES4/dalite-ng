import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("peerinst", "0061_auto_20190117_1926")]

    operations = [
        migrations.CreateModel(
            name="ShownRationale",
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
                    "shown_answer",
                    models.ForeignKey(
                        related_name="shown_answer",
                        to="peerinst.Answer",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "shown_for_answer",
                    models.ForeignKey(
                        related_name="shown_for_answer",
                        to="peerinst.Answer",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="answer",
            name="shown_rationales",
            field=models.ManyToManyField(
                related_name="shown_rationales_all",
                through="peerinst.ShownRationale",
                to="peerinst.Answer",
                blank=True,
            ),
        ),
    ]
