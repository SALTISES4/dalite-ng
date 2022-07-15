from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0005_auto_20150831_1417'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='fake_attributions',
            field=models.BooleanField(default=False, help_text='Add random fake attributions consisting of username and country to rationales.  You can configure the lists of fake values and countries from the start page of the admin interface.', verbose_name='Add fake attributions'),
        ),
    ]
