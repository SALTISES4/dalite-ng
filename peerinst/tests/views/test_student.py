# -*- coding: utf-8 -*-


import json

from django.contrib.auth.models import User
from django.urls import reverse

from peerinst.models import Student, StudentGroupMembership
from peerinst.students import create_student_token
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.student import add_to_group, login_student


def test_index_fail_on_no_logged_in_and_no_token(client):
    resp = client.get(reverse("student-page"))
    assert resp.status_code == 403
    assert any(t.name == "403.html" for t in resp.templates)
    assert (
        "You must be a logged in student to access this resource."
        in resp.content.decode()
    )


def test_index_fail_on_logged_in_not_student(client, user):
    assert client.login(username=user.username, password="test")

    resp = client.get(reverse("student-page"))
    assert resp.status_code == 403
    assert any(t.name == "403.html" for t in resp.templates)
    assert (
        "You must be a logged in student to access this resource."
        in resp.content.decode()
    )


def test_index_student_logged_in(client, student):
    assert login_student(client, student)

    resp = client.get(reverse("student-page"))
    assert resp.status_code == 200
    assert any(t.name == "peerinst/student/index.html" for t in resp.templates)
    assert student.student.email in resp.content.decode()


def test_index_student_not_logged_in_token(client, student):
    token = create_student_token(
        student.student.username, student.student.email
    )

    resp = client.get(reverse("student-page") + "?token={}".format(token))
    assert resp.status_code == 200
    assert any(t.name == "peerinst/student/index.html" for t in resp.templates)
    assert student.student.email in resp.content.decode()


def test_index_student_logged_in_token_same_user(client, student):
    assert login_student(client, student)

    token = create_student_token(
        student.student.username, student.student.email
    )

    resp = client.get(reverse("student-page") + "?token={}".format(token))
    assert resp.status_code == 200
    assert any(t.name == "peerinst/student/index.html" for t in resp.templates)
    assert student.student.email in resp.content.decode()


def test_index_student_logged_in_token_different_user(client, students):
    assert login_student(client, students[0])

    token = create_student_token(
        students[1].student.username, students[1].student.email
    )

    resp = client.get(reverse("student-page") + "?token={}".format(token))
    assert resp.status_code == 200
    assert any(t.name == "peerinst/student/index.html" for t in resp.templates)
    assert students[1].student.email in resp.content.decode()
    assert not students[0].student.email in resp.content.decode()


def test_index_new_student(client, student):
    student.student.is_active = False
    student.student.save()

    token = create_student_token(
        student.student.username, student.student.email
    )

    assert not Student.objects.get(student=student.student).student.is_active

    resp = client.get(reverse("student-page") + "?token={}".format(token))
    assert resp.status_code == 200
    assert any(t.name == "peerinst/student/index.html" for t in resp.templates)
    assert student.student.email in resp.content.decode()
    assert Student.objects.get(student=student.student).student.is_active


def test_leave_group_no_data(client, student):
    assert login_student(client, student)
    resp = client.post(reverse("student-leave-group"))
    assert resp.status_code == 400
    assert any(t.name == "400.html" for t in resp.templates)
    assert "Wrong data type was sent." in resp.content.decode()


def test_leave_group_wrong_data(client, student, group):
    assert login_student(client, student)
    data = {}
    resp = client.post(
        reverse("student-leave-group"),
        json.dumps(data),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert any(t.name == "400.html" for t in resp.templates)
    assert "There are missing parameters." in resp.content.decode()


def test_leave_group_is_member_of_group(client, student, group):
    student.groups.add(group)
    assert login_student(client, student)
    StudentGroupMembership.objects.get_or_create(student=student, group=group)

    assert group in student.groups.all()
    assert group in student.student_groups.all()
    assert StudentGroupMembership.objects.get(
        student=student, group=group
    ).current_member
    data = {"username": student.student.username, "group_name": group.name}
    resp = client.post(
        reverse("student-leave-group"),
        json.dumps(data),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert group in student.groups.all()
    assert not StudentGroupMembership.objects.get(
        student=student, group=group
    ).current_member


def test_leave_group_is_not_member_of_group(client, student, group):
    assert login_student(client, student)
    data = {"username": student.student.username, "group_name": group.name}
    resp = client.post(
        reverse("student-leave-group"),
        json.dumps(data),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert group not in student.groups.all()


def test_login_page(client):
    resp = client.get(reverse("student-login"))
    assert resp.status_code == 200
    assert any(t.name == "peerinst/student/login.html" for t in resp.templates)


def test_send_signin_link_single_account(client, student):
    data = {"email": student.student.email}
    resp = client.post(reverse("student-send-signin-link"), data)
    assert resp.status_code == 200
    assert any(
        t.name == "peerinst/student/login_confirmation.html"
        for t in resp.templates
    )
    assert "Email sent" in resp.content.decode()


def test_send_signin_link_multiple_accounts(client, student):
    Student.objects.create(
        student=User.objects.create_user(
            username="test", email=student.student.email
        )
    )
    data = {"email": student.student.email}
    resp = client.post(reverse("student-send-signin-link"), data)
    assert resp.status_code == 200
    assert any(
        t.name == "peerinst/student/login_confirmation.html"
        for t in resp.templates
    )
    assert "Email sent" in resp.content.decode()


def test_send_signin_link_wrong_method(client):
    resp = client.get(reverse("student-send-signin-link"))
    assert resp.status_code == 405


def test_send_signin_link_missing_params(client):
    resp = client.post(reverse("student-send-signin-link"))
    assert resp.status_code == 400
    assert any(t.name == "400.html" for t in resp.templates)
    assert "There are missing parameters." in resp.content.decode()


def test_update_student_id(client, student, group):
    assert login_student(client, student)
    add_to_group(student, group)

    data = {"student_id": "1234567", "group_name": group.name}

    resp = client.post(
        reverse("student-change-id"),
        json.dumps(data),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert (
        StudentGroupMembership.objects.get(
            student=student, group=group
        ).student_school_id
        == data["student_id"]
    )


def test_update_student_id__not_logged_in(client):
    resp = client.post(reverse("student-change-id"))
    assert resp.status_code == 403
    assert any(t.name == "403.html" for t in resp.templates)


def test_update_student_id__no_data(client, student, group):
    assert login_student(client, student)
    add_to_group(student, group)

    resp = client.post(reverse("student-change-id"))
    assert resp.status_code == 400
    assert any(t.name == "400.html" for t in resp.templates)


def test_update_student_id__wrong_data(client, student, group):
    assert login_student(client, student)
    add_to_group(student, group)

    data = {"group_name": group.name}

    resp = client.post(
        reverse("student-change-id"),
        json.dumps(data),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert any(t.name == "400.html" for t in resp.templates)

    data = {"student_id": "1234567"}

    resp = client.post(
        reverse("student-change-id"),
        json.dumps(data),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert any(t.name == "400.html" for t in resp.templates)

    data = {}

    resp = client.post(
        reverse("student-change-id"),
        json.dumps(data),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert any(t.name == "400.html" for t in resp.templates)


def test_update_student_id__wrong_group(client, student, group):
    assert login_student(client, student)
    add_to_group(student, group)

    data = {"student_id": "1234567", "group_name": group.name + "fdsafdsaf"}

    resp = client.post(
        reverse("student-change-id"),
        json.dumps(data),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert any(t.name == "400.html" for t in resp.templates)


def test_update_student_id__no_group_membership(client, student, group):
    assert login_student(client, student)

    data = {"student_id": "1234567", "group_name": group.name}

    resp = client.post(
        reverse("student-change-id"),
        json.dumps(data),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert any(t.name == "400.html" for t in resp.templates)
