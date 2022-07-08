from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("peerinst", "0059_remove_studentnotification_hover_text")]

    operations = [
        migrations.AlterField(
            model_name="question",
            name="category",
            field=models.ManyToManyField(
                help_text="Optional. Select categories for this question. "
                "You can select multiple categories.",
                db_constraint="Categories",
                to="peerinst.Category",
                blank=True,
            ),
        )
    ]
