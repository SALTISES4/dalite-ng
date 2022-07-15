from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("peerinst", "0063_auto_20190123_1523")]

    operations = [
        migrations.RenameField(
            model_name="answer", old_name="time", new_name="datetime_first"
        ),
        migrations.AlterField(
            model_name="question",
            name="category",
            field=models.ManyToManyField(
                blank=True,
                help_text="Optional. Select categories for this question. "
                "You can select multiple categories.",
                related_name="Categories",
                to="peerinst.Category",
            ),
        ),
    ]
