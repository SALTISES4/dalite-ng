import time
from datetime import datetime, timedelta

import pytz
from django.core import mail

from peerinst.scheduled import verify_assignment_due_dates

from .fixtures import *  # noqa F403


def test_verify_assignment_due_dates(
    student_group_assignment, students_with_assignment
):
    #  student_group_assignment.due_date = datetime.now(pytz.utc) + timedelta(
    #  days=1
    #  )
    #  student_group_assignment.reminder_days = 3
    #  student_group_assignment.save()
    #
    #  verify_assignment_due_dates(check_every=1 / 3600)
    #  time.sleep(1)
    #
    #  assert len(mail.outbox) == len(students_with_assignment)
    #
    #  verify_assignment_due_dates(check_every=1 / 3600)
    #  time.sleep(1)
    #
    #  assert len(mail.outbox) == 2 * len(students_with_assignment)
    pass
