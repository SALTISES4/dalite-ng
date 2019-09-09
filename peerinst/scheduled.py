# import threading
import logging

# from datetime import datetime, timedelta

# from .models import StudentGroupAssignment
logger = logging.getLogger("peerinst-models")


def start_scheduled_events():
    """
    Starts all events which happen on specific dates (such as assignment about
    to expire emails).
    """
    verify_assignment_due_dates()


def stop_scheduled_events():
    pass


def verify_assignment_due_dates(check_every=1):
    """
    Verifies each day if each assignment is about to expire and not done and
    adds a student notification for it and possibly sends an email.

    Parameters
    ----------
    check_every : int or float
        Days or fraction of days after which to recheck the assignment due
        dates
    """
    #  for assignment in StudentGroupAssignment.objects.all():
    #  assignment.check_reminder_status()
    #
    #  next_check = datetime.now() + timedelta(days=check_every)
    #  if round(check_every) == check_every:
    #  next_check.replace(hour=0, minute=0, second=0, microsecond=0)
    #  else:
    #  next_check.replace(minute=0, second=0, microsecond=0)
    #
    #  timer = threading.Timer(
    #  (next_check - datetime.now()).seconds, verify_assignment_due_dates
    #  )
    #  timer.setDaemon(True)
    #  timer.start()
    pass
