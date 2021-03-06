# Generated by Django 2.2.9 on 2020-03-16 05:07

from django.db import migrations, models
import django.db.models.deletion
import peerinst.models.question


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0093_auto_20200219_2152'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Enter the name of a new subject.', max_length=100, unique=True, validators=[peerinst.models.question.no_hyphens], verbose_name='Subject name')),
                ('categories', models.ManyToManyField(blank=True, related_name='subjects', to='peerinst.Category')),
                ('discipline', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='peerinst.Discipline')),
            ],
            options={
                'verbose_name': 'subject',
                'verbose_name_plural': 'subjects',
            },
        ),
    ]
