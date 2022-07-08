import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("peerinst", "0024_auto_20180221_0236"),
    ]

    operations = [
        migrations.AlterField(
            model_name="blinkanswer",
            name="voting_round",
            field=models.ForeignKey(
                default=1,
                to="peerinst.BlinkRound",
                on_delete=django.db.models.deletion.CASCADE,
            ),
            preserve_default=False,
        ),
    ]
