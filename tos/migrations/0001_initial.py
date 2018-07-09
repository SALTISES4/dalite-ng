# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Consent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('accepted', models.BooleanField()),
                ('datetime', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Tos',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', models.PositiveIntegerField()),
                ('hash', models.CharField(max_length=32, editable=False)),
                ('text', models.TextField()),
                ('created', models.DateTimeField(auto_now=True)),
                ('current', models.BooleanField()),
                ('role', models.CharField(max_length=2, choices=[(b'st', b'student'), (b'te', b'teacher')])),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='tos',
            unique_together=set([('role', 'hash'), ('role', 'version')]),
        ),
        migrations.AddField(
            model_name='consent',
            name='tos',
            field=models.ForeignKey(to='tos.Tos'),
        ),
        migrations.AddField(
            model_name='consent',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
