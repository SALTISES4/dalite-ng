# Generated by Django 2.2.24 on 2021-07-21 00:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0103_remove_student_groups'),
    ]

    operations = [
        migrations.RenameField(
            model_name='student',
            old_name='student_groups',
            new_name='groups',
        ),
    ]
