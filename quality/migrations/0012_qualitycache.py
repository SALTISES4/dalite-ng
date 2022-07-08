from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("quality", "0011_auto_20190502_1522")]

    operations = [
        migrations.CreateModel(
            name="QualityCache",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("answer", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "hash",
                    models.CharField(
                        db_index=True, max_length=32, unique=True
                    ),
                ),
                ("quality", models.FloatField()),
                ("qualities", models.TextField()),
            ],
        )
    ]
