import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("peerinst", "0031_answer_time"),
    ]

    operations = [
        migrations.CreateModel(
            name="VerifiedDomain",
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
                    "domain",
                    models.CharField(
                        help_text="Teacher-only email domain, if available.  Email addresses with these domains will be treated as verified.",
                        max_length=100,
                    ),
                ),
                (
                    "institution",
                    models.ForeignKey(
                        to="peerinst.Institution",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={"verbose_name": "verified email domain name",},
        ),
    ]
