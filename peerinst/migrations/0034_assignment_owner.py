from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('peerinst', '0033_studentgroup_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='owner',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
