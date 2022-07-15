import json
from unittest import mock

from django.http import HttpResponse
from django.urls import reverse

from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.student import login_student
from reputation.tests.fixtures import *  # noqa


def test_reputation__teacher(client, teacher):
    data = {"reputation_type": "teacher"}
    client.login(username=teacher.user.username, password="test")

    with mock.patch(
        "reputation.views.reputation.teacher_reputation",
        return_value=HttpResponse(""),
    ):
        resp = client.post(
            reverse("reputation:reputation"),
            json.dumps(data),
            content_type="application/json",
        )
        assert resp.status_code == 200


def test_reputation__student(client, student):
    data = {"reputation_type": "student"}
    login_student(client, student)

    with mock.patch(
        "reputation.views.reputation.student_reputation",
        return_value=HttpResponse(""),
    ):
        resp = client.post(
            reverse("reputation:reputation"),
            json.dumps(data),
            content_type="application/json",
        )
        assert resp.status_code == 200


def test_reputation__missing_args(client, teacher):
    data = {}
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("reputation:reputation"),
        json.dumps(data),
        content_type="application/json",
    )

    assert resp.status_code == 400
    assert resp.template_name == "400.html"


def test_reputation__wrong_type(client, teacher):
    data = {"reputation_type": "wrong"}
    client.login(username=teacher.user.username, password="test")

    resp = client.post(
        reverse("reputation:reputation"),
        json.dumps(data),
        content_type="application/json",
    )

    assert resp.status_code == 400
    assert resp.template_name == "400.html"
