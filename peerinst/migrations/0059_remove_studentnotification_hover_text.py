from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("peerinst", "0058_merge")]

    operations = [
        migrations.RemoveField(
            model_name="studentnotification", name="hover_text"
        )
    ]
