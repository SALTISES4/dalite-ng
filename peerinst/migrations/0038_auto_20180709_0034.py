import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0037_question_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
