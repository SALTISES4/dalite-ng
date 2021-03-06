import pytest

from peerinst.models import StudentNotification, StudentNotificationType

from .fixtures import *  # noqa F403


def test_create_new_assignment(student, student_assignment):
    data = {
        "type_": "new_assignment",
        "student": student,
        "assignment": student_assignment,
    }
    assert not StudentNotification.objects.filter(student=student).exists()

    StudentNotification.create(**data)

    assert StudentNotification.objects.filter(
        student=student, notification__type=data["type_"]
    ).exists()


def test_create_new_assignment_no_assignment(student):
    data = {"type_": "new_assignment", "student": student}
    assert not StudentNotification.objects.filter(student=student).exists()

    with pytest.raises(ValueError):
        StudentNotification.create(**data)


def test_create_assignment_about_to_expire(student, student_assignment):
    data = {
        "type_": "assignment_about_to_expire",
        "student": student,
        "assignment": student_assignment,
    }
    assert not StudentNotification.objects.filter(student=student).exists()

    StudentNotification.create(**data)

    assert StudentNotification.objects.filter(
        student=student, notification__type=data["type_"]
    ).exists()


def test_create_assignment_about_to_expire_no_assignment(student):
    data = {"type_": "assignment_about_to_expire", "student": student}
    assert not StudentNotification.objects.filter(student=student).exists()

    with pytest.raises(ValueError):
        StudentNotification.create(**data)


def test_create_assignment_due_date_changed(student, student_assignment):
    data = {
        "type_": "assignment_due_date_changed",
        "student": student,
        "assignment": student_assignment,
    }
    assert not StudentNotification.objects.filter(student=student).exists()

    StudentNotification.create(**data)

    assert StudentNotification.objects.filter(
        student=student, notification__type=data["type_"]
    ).exists()


def test_create_assignment_due_date_changed_no_assignment(student):
    data = {"type_": "assignment_due_date_changed", "student": student}
    assert not StudentNotification.objects.filter(student=student).exists()

    with pytest.raises(ValueError):
        StudentNotification.create(**data)


def test_create__unkown_type(student):
    StudentNotificationType.objects.create(type="new_type", icon="assignment")
    data = {"type_": "new_type", "student": student}
    assert not StudentNotification.objects.filter(student=student).exists()

    with pytest.raises(NotImplementedError):
        StudentNotification.create(**data)
