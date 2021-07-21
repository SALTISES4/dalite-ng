import hashlib

import pytest
from django.core import mail
from django.urls import reverse

from peerinst.models import (
    Student,
    StudentAssignment,
    StudentGroupMembership,
    StudentNotification,
)
from peerinst.students import create_student_token
from peerinst.tests.generators import add_students, new_students

from .fixtures import *  # noqa F403

MAX_USERNAME_LENGTH = 30


def test_get_or_create__new():
    data = new_students(1)[0]

    student, created = Student.get_or_create(**data)
    username = hashlib.md5(data["email"].encode()).hexdigest()[
        :MAX_USERNAME_LENGTH
    ]

    assert isinstance(student, Student)
    assert created
    assert student.student.email == data["email"]
    assert student.student.username == username
    assert len(Student.objects.all()) == 1


def test_get_or_create__get():
    data = new_students(1)[0]
    add_students([data])

    student, created = Student.get_or_create(**data)
    username = hashlib.md5(data["email"].encode()).hexdigest()[
        :MAX_USERNAME_LENGTH
    ]

    assert isinstance(student, Student)
    assert not created
    assert student.student.email == data["email"]
    assert student.student.username == username
    assert len(Student.objects.all()) == 1


def test_send_email__confirmation(student):
    err = student.send_email(mail_type="confirmation")

    assert err is None
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Confirm your myDALITE account"


def test_send_email__confirmation_with_localhost(student):
    student.student.email = "fake-email@localhost"
    student.student.save()

    err = student.send_email(mail_type="confirmation")

    assert err is None
    assert not mail.outbox


def test_send_email__signin(student):
    err = student.send_email(mail_type="signin")

    assert err is None
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Sign in to your myDALITE account"


def test_send_email__signin_with_localhost(student):
    student.student.email = "fake-email@localhost"
    student.student.save()
    err = student.send_email(mail_type="signin")

    assert err is None
    assert not mail.outbox


def test_send_email__new_group(student, group):
    err = student.send_email(mail_type="new_group", group=group)
    assert err is None

    assert len(mail.outbox) == 1

    assert mail.outbox[
        0
    ].subject == "You've successfully been registered to group {}".format(
        group.title
    )


def test_send_email__new_group_with_localhost(student, group):
    student.student.email = "fake-email@localhost"
    student.student.save()
    err = student.send_email(mail_type="new_group", group=group)

    assert err is None
    assert not mail.outbox


def test_send_email__new_group_missing_group(student, group):
    with pytest.raises(ValueError):
        student.send_email(mail_type="new_group")


def test_send_email__wrong_type(student):
    err = student.send_email(mail_type="wrong_type")

    assert err == "The `mail_type` wasn't in the allowed types."
    assert not mail.outbox


def test_send_email__no_email(student):
    student.student.email = ""
    student.student.save()

    err = student.send_email(mail_type="confirmation")

    assert err == "There is no email associated with user {}.".format(
        student.student.username
    )
    assert not mail.outbox


def test_join_group(student, group):
    student.join_group(group)

    assert group in student.groups.all()
    assert group in student.current_groups
    assert group not in student.old_groups
    assert not mail.outbox


def test_join_group_mail_new_group(student, group):
    student.join_group(group, mail_type="new_group")

    assert group in student.student_groups.all()
    assert group in student.current_groups
    assert group not in student.old_groups
    assert len(mail.outbox) == 1


def test_join_group_mail_confirmation(student, group):
    student.join_group(group, mail_type="confirmation")

    assert group in student.student_groups.all()
    assert group in student.current_groups
    assert group not in student.old_groups
    assert len(mail.outbox) == 1


def test_join_group_existing_assignments(student, group_assignment):
    group_assignment.distribute()
    assert not StudentAssignment.objects.filter(
        student=student, group_assignment=group_assignment
    ).exists()

    student.join_group(group_assignment.group)

    assert group_assignment.group in student.student_groups.all()
    assert group_assignment.group in student.current_groups
    assert group_assignment.group not in student.old_groups

    assert StudentAssignment.objects.filter(
        student=student, group_assignment=group_assignment
    ).exists()
    assert not mail.outbox


def test_leave_group(student, group):
    student.groups.add(group)
    StudentGroupMembership.objects.create(student=student, group=group)
    assert group in student.groups.all()
    assert group in student.student_groups.all()

    student.leave_group(group)

    assert group in student.student_groups.all()
    assert group not in student.current_groups
    assert group in student.old_groups


def test_leave_group__doesnt_exist(student, group):
    student.leave_group(group)

    assert group not in student.student_groups.all()
    assert group not in student.current_groups
    assert group not in student.old_groups


def test_add_assignment(student, group_assignment):
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
    assert (
        StudentNotification.objects.get(
            student=student, notification__type="new_assignment"
        ).link.split("/")[-1]
        == reverse(
            "live",
            kwargs={
                "assignment_hash": group_assignment.hash,
                "token": create_student_token(
                    student.student.username, student.student.email
                ),
            },
        ).split("/")[-1]
    )

    assert len(mail.outbox) == 1

    assert mail.outbox[0].subject == "New assignment for group {}".format(
        group_assignment.group.title
    )


def test_add_assignment__assignment_exists(student, group_assignment):
    group_assignment.distribute()
    student.join_group(group_assignment.group)

    assert StudentAssignment.objects.filter(
        student=student, group_assignment=group_assignment
    ).exists()
    assert StudentNotification.objects.filter(
        student=student, notification__type="new_assignment"
    ).exists()

    student.add_assignment(group_assignment)

    assert (
        StudentAssignment.objects.filter(
            student=student, group_assignment=group_assignment
        ).count()
        == 1
    )
    assert StudentNotification.objects.filter(
        student=student, notification__type="new_assignment"
    ).exists()
    assert (
        StudentNotification.objects.get(
            student=student, notification__type="new_assignment"
        ).link.split("/")[-1]
        == reverse(
            "live",
            kwargs={
                "assignment_hash": group_assignment.hash,
                "token": create_student_token(
                    student.student.username, student.student.email
                ),
            },
        ).split("/")[-1]
    )
