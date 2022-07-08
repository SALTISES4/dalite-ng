from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('peerinst', '0038_auto_20180709_0034'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='image',
            field=models.ImageField(help_text='Optional. An image to include after the question text.  Accepted formats: .jpg, .jpeg, .png, .gif', upload_to='images', null=True, verbose_name='Question image', blank=True),
        ),
    ]
