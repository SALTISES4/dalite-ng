from django.core.management.base import BaseCommand

from peerinst.models import Answer


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for answer in Answer.objects.all():
            answer.update_rationale_shown_count()
            answer.update_rationale_chosen_count()
            print(
                answer.rationale_chosen_counter, answer.rationale_shown_counter
            )
        self.stdout.write("Answer counts have been updated.")
