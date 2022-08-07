from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("peerinst", "0040_auto_20180720_1519"),
    ]

    operations = [
        migrations.CreateModel(
            name="LtiEvent",
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
                ("event_type", models.CharField(max_length=100)),
                ("event_log", models.JSONField(default={})),
                (
                    "timestamp",
                    models.DateTimeField(auto_now_add=True, null=True),
                ),
            ],
        ),
    ]
