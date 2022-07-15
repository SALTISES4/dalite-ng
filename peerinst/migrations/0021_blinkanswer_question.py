import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("peerinst", "0020_auto_20180219_0457"),
    ]

    operations = [
        migrations.AddField(
            model_name="blinkanswer",
            name="question",
            field=models.ForeignKey(
                default=1,
                to="peerinst.BlinkQuestion",
                on_delete=django.db.models.deletion.CASCADE,
            ),
            preserve_default=False,
        ),
    ]
