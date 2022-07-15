import datetime
import logging
import time

import pytz
from django.core.management.base import BaseCommand

from peerinst.util import (
    load_shown_rationales_from_ltievent_logs,
    make_daterange,
)

LOGGER = logging.getLogger("peerinst")


class Command(BaseCommand):
    help = """
    make ShownRationale objects from LtiEvents.
    Output should be directed to a log file
    Since this function takes a long time on production db,
    do one month at a time
    """

    def handle(self, *args, **options):
        start = time.time()

        start_date = datetime.datetime(
            day=1, month=9, year=2018, tzinfo=pytz.utc
        )
        end_date = datetime.datetime(
            day=31, month=12, year=2018, tzinfo=pytz.utc
        )

        for day_of_logs in make_daterange(start_date, end_date):
            print(day_of_logs)
            load_shown_rationales_from_ltievent_logs(day_of_logs)

        print("Completed loading shown rationales")
        print(f"Took {time.time() - start:.2f} seconds")
