# Generated by Django 1.11.20 on 2019-05-22 18:17


import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("reputation", "0002_nquestionscriterion")]

    operations = [
        migrations.CreateModel(
            name="ReputationHistory",
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
                ("date", models.DateField(auto_now_add=True)),
                (
                    "reputation_value",
                    models.FloatField(blank=True, editable=False, null=True),
                ),
                ("reputation_details", models.TextField(editable=False)),
                (
                    "reputation",
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="reputation.Reputation",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="reputationhistory",
            unique_together={("reputation", "date")},
        ),
    ]
