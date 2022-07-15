import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("peerinst", "0022_auto_20180220_0308"),
    ]

    operations = [
        migrations.CreateModel(
            name="BlinkRound",
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
                ("activate_time", models.DateTimeField(blank=True)),
                ("deactivate_time", models.DateTimeField(blank=True)),
            ],
        ),
        migrations.RemoveField(
            model_name="blinkquestion", name="activate_time",
        ),
        migrations.RemoveField(
            model_name="blinkquestion", name="deactivate_time",
        ),
        migrations.AddField(
            model_name="blinkquestion",
            name="time_limit",
            field=models.PositiveSmallIntegerField(
                null=True, verbose_name="Time limit"
            ),
        ),
        migrations.AddField(
            model_name="blinkround",
            name="question",
            field=models.ForeignKey(
                to="peerinst.BlinkQuestion",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="blinkanswer",
            name="voting_round",
            field=models.ForeignKey(
                to="peerinst.BlinkRound",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
