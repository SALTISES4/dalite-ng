# Generated by Django 1.11.20 on 2019-05-17 02:50


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("peerinst", "0080_auto_20190516_1956")]

    operations = [
        migrations.AddField(
            model_name="collection",
            name="featured",
            field=models.BooleanField(default=False),
        )
    ]
