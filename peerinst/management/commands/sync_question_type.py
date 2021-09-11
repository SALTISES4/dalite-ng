from django.core.management.base import BaseCommand

from peerinst.models import Question


class Command(BaseCommand):
    help = (
        "Ensure alignment between question type and second_answer_needed "
        "fields"
    )

    def handle(self, *args, **options):
        count = 0
        for q in Question.objects.filter(type="PI"):
            if q.second_answer_needed is False:
                q.second_answer_needed = True
                q.save()
                count += 1

        print(f"{count} PI questions fixed.")

        count = 0
        for q in Question.objects.filter(type="RO"):
            if q.second_answer_needed is True:
                q.second_answer_needed = False
                q.save()
                count += 1

        print(f"{count} RO questions fixed.")
