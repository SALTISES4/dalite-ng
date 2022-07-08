from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0004_auto_20150831_1122'),
    ]

    operations = [
        migrations.CreateModel(
            name='FakeCountry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
            ],
            options={
                'verbose_name': 'fake country',
                'verbose_name_plural': 'fake countries',
            },
        ),
        migrations.CreateModel(
            name='FakeUsername',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
            ],
            options={
                'verbose_name': 'fake username',
                'verbose_name_plural': 'fake usernames',
            },
        ),
        migrations.AlterField(
            model_name='question',
            name='rationale_selection_algorithm',
            field=models.CharField(default='prefer_expert_and_highly_voted', help_text='The algorithm to use for choosing the rationales presented to students during question review.  This option is ignored if you selected sequential review.', max_length=100, verbose_name='Rationale selection algorithm', choices=[('simple', 'Simple random rationale selection'), ('prefer_expert_and_highly_voted', 'Prefer expert and highly votes rationales')]),
        ),
    ]
