from django.core.management.base import BaseCommand

from peerinst.models import Question


class Command(BaseCommand):
    help = (
        "Basic sanity check, for now checks database connectivity by "
        "executing a query"
    )

    def handle(self, *args, **options):
        print(
            ("There are this many questions", Question.objects.all().count())
        )
