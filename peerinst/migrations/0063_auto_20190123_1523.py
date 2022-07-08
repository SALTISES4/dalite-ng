import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("peerinst", "0062_auto_20190122_2110")]

    operations = [
        migrations.AlterField(
            model_name="shownrationale",
            name="shown_answer",
            field=models.ForeignKey(
                related_name="shown_answer",
                to="peerinst.Answer",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        )
    ]
