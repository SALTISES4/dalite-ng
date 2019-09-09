import json

import mock
from django.core.urlresolvers import reverse

from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher


def test_gradebook_task_result__ready(client, teacher):
    assert login_teacher(client, teacher)

    with mock.patch("peerinst.views.teacher.AsyncResult") as AsyncResult:
        result = mock.Mock()
        result.ready.return_value = True
        AsyncResult.return_value = result

        resp = client.post(
            reverse("teacher-gradebook--result"),
            json.dumps({"task_id": 1}),
            content_type="application/json",
        )

        assert resp.status_code == 200


def test_gradebook_task_result__not_ready(client, teacher):
    assert login_teacher(client, teacher)

    with mock.patch("peerinst.views.teacher.AsyncResult") as AsyncResult:
        result = mock.Mock()
        result.ready.return_value = False
        AsyncResult.return_value = result

        resp = client.post(
            reverse("teacher-gradebook--result"),
            json.dumps({"task_id": 1}),
            content_type="application/json",
        )

        assert resp.status_code == 202


def test_gradebook_task_result__celery_error(client, teacher):
    assert login_teacher(client, teacher)

    with mock.patch("peerinst.views.teacher.AsyncResult") as AsyncResult:
        result = mock.Mock()
        result.ready.side_effect = AttributeError()
        AsyncResult.return_value = result

        resp = client.post(
            reverse("teacher-gradebook--result"),
            json.dumps({"task_id": 1}),
            content_type="application/json",
        )

        assert resp.status_code == 500


def test_gradebook_task_result__missing_params(client, teacher):
    assert login_teacher(client, teacher)

    resp = client.post(
        reverse("teacher-gradebook--result"),
        json.dumps({}),
        content_type="application/json",
    )

    assert resp.status_code == 400
