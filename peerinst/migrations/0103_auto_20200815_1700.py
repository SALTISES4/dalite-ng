# Generated by Django 2.2.14 on 2020-08-15 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0102_auto_20200807_0403'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answerannotation',
            name='note',
            field=models.CharField(blank=True, max_length=2000, null=True),
        ),
    ]
