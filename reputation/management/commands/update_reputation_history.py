import logging
from datetime import datetime

from django.core.management.base import BaseCommand

from reputation.models import Reputation, ReputationHistory

logger = logging.getLogger("reputation")


class Command(BaseCommand):
    help = "Compute and save the reputations in the history."

    def handle(self, *args, **options):
        reputations = Reputation.objects.all()

        n = reputations.count()
        step = 1.0 / n * 100
        progress = 0

        for reputation in reputations.iterator():
            ReputationHistory.create(reputation)
            progress = progress + step
            print(
                f"{datetime.now()} - ({progress:>6.2f}%) -"
                + " Updating reputations"
            )
