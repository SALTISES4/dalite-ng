from django.db import migrations


def copy_datetime_first_to_datetime_second_old_answers(apps, _):
    Answer = apps.get_model("peerinst", "Answer")

    for answer in Answer.objects.exclude(datetime_first__isnull=True):
        if answer.datetime_start is None:
            answer.datetime_second = answer.datetime_first
            answer.datetime_first = None
            answer.save()


class Migration(migrations.Migration):

    dependencies = [("peerinst", "0069_auto_20190221_0458")]

    operations = [
        migrations.RunPython(
            copy_datetime_first_to_datetime_second_old_answers
        )
    ]
