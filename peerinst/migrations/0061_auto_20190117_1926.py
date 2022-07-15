from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("peerinst", "0060_auto_20190111_2112")]

    operations = [
        migrations.AlterField(
            model_name="studentgroupassignment",
            name="distribution_date",
            field=models.DateTimeField(null=True, editable=False, blank=True),
        )
    ]
