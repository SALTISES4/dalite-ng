from django.core import mail
from django.utils import timezone

from peerinst.models import (
    StudentAssignment,
    StudentGroup,
    StudentGroupAssignment,
    StudentGroupMembership,
    StudentNotification,
)

from .fixtures import *


def test_join_group_lti(django_assert_num_queries, student, group, assignment):
    group.mode_created = group.LTI
    group.save()

    student.join_group(group)

    StudentGroupAssignment.objects.create(
        group=group, assignment=assignment, distribution_date=timezone.now()
    )

    membership = StudentGroupMembership.objects.get(
        group=group, student=student
    )

    assert group in student.groups.all()
    assert group in student.current_groups
    assert group not in student.old_groups

    assert membership.send_emails is False
    assert StudentNotification.objects.filter(student=student).count() == 0
    assert not mail.outbox


def test_not_send_email(student, group):
    group.mode_created = StudentGroup.LTI_STANDALONE
    group.save()
    mail_types = ["new_group", "confirmation", "signin"]
    for mail_type in mail_types:
        _ = student.send_email(mail_type=mail_type, group=group)
        assert len(mail.outbox) == 0


def test_not_send_email_new_assignment(student, group, group_assignment):
    group.mode_created = StudentGroup.LTI_STANDALONE
    group.save()

    student.join_group(group_assignment.group)

    StudentAssignment.objects.filter(
        student=student, group_assignment=group_assignment
    ).delete()
    StudentNotification.objects.filter(
        student=student, notification__type="new_assignment"
    ).delete()

    student.add_assignment(group_assignment)

    assert StudentAssignment.objects.filter(
        student=student, group_assignment=group_assignment
    ).exists()
    assert StudentNotification.objects.filter(
        student=student, notification__type="new_assignment"
    ).exists()

    assert len(mail.outbox) == 0
