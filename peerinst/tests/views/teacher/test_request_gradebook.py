import json

import mock
from celery.result import AsyncResult
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from peerinst.models import RunningTask
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher


def test_request_gradebook__group(client, teacher, group):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)

    class AsyncResultMock(AsyncResult):
        def __new__(cls):
            return mock.mock(spec=cls)

    with mock.patch(
        "peerinst.views.teacher.compute_gradebook_async"
    ) as compute_gradebook_async, mock.patch(
        "peerinst.views.teacher.AsyncResult", new=AsyncResultMock
    ):
        result = mock.Mock(spec=AsyncResultMock)
        result.id = 1
        compute_gradebook_async.return_value = result

        resp = client.post(
            reverse("teacher-gradebook--request"),
            json.dumps({"group_id": group.pk}),
            content_type="application/json",
        )
        compute_gradebook_async.assert_called_with(group.pk, None)

    assert resp.status_code == 201
    data = json.loads(resp.content)
    assert data["id"] == 1
    assert data[
        "description"
    ] == "gradebook for group <strong>{}</strong>".format(group.name)
    assert not data["completed"]

    assert RunningTask.objects.filter(id=1).exists()


def test_request_gradebook__assignment(
    client, teacher, group, student_group_assignment
):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)

    class AsyncResultMock(AsyncResult):
        def __new__(cls):
            return mock.mock(spec=cls)

    with mock.patch(
        "peerinst.views.teacher.compute_gradebook_async"
    ) as compute_gradebook_async, mock.patch(
        "peerinst.views.teacher.AsyncResult", new=AsyncResultMock
    ):
        result = mock.Mock(spec=AsyncResultMock)
        result.id = 1
        compute_gradebook_async.return_value = result

        resp = client.post(
            reverse("teacher-gradebook--request"),
            json.dumps(
                {
                    "group_id": group.pk,
                    "assignment_id": student_group_assignment.pk,
                }
            ),
            content_type="application/json",
        )

        compute_gradebook_async.assert_called_with(
            group.pk, student_group_assignment.pk
        )

    assert resp.status_code == 201
    data = json.loads(resp.content)
    assert data["id"] == 1
    assert data[
        "description"
    ] == "gradebook for assignment {} and group {}".format(
        student_group_assignment.assignment.identifier, group.name
    )
    assert not data["completed"]

    assert RunningTask.objects.filter(id=1).exists()


def test_request_gradebook__group__no_celery(client, teacher, group):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)

    n = RunningTask.objects.count()

    with mock.patch(
        "peerinst.views.teacher.compute_gradebook_async"
    ) as compute_gradebook_async, mock.patch(
        "peerinst.views.teacher.download_gradebook"
    ) as download_gradebook:
        result = mock.Mock()
        compute_gradebook_async.return_value = result
        download_gradebook.return_value = HttpResponse()

        resp = client.post(
            reverse("teacher-gradebook--request"),
            json.dumps({"group_id": group.pk}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        compute_gradebook_async.assert_called_with(group.pk, None)
        download_gradebook.assert_called_with(mock.ANY, results=result)

    assert RunningTask.objects.count() == n


def test_request_gradebook__assignment__no_celery(
    client, teacher, group, student_group_assignment
):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)

    n = RunningTask.objects.count()

    with mock.patch(
        "peerinst.views.teacher.compute_gradebook_async"
    ) as compute_gradebook_async, mock.patch(
        "peerinst.views.teacher.download_gradebook"
    ) as download_gradebook:
        result = mock.Mock()
        compute_gradebook_async.return_value = result
        download_gradebook.return_value = HttpResponse()

        resp = client.post(
            reverse("teacher-gradebook--request"),
            json.dumps(
                {
                    "group_id": group.pk,
                    "assignment_id": student_group_assignment.pk,
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        compute_gradebook_async.assert_called_with(
            group.pk, student_group_assignment.pk
        )
        download_gradebook.assert_called_with(mock.ANY, results=result)

    assert RunningTask.objects.count() == n


def test_request_gradebook__missing_params(client, teacher, group):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)

    n = RunningTask.objects.count()

    resp = client.post(
        reverse("teacher-gradebook--request"),
        json.dumps({}),
        content_type="application/json",
    )

    assert resp.status_code == 400
    assert RunningTask.objects.count() == n


def test_request_gradebook__invalid_group(client, teacher):
    assert login_teacher(client, teacher)

    n = RunningTask.objects.count()

    resp = client.post(
        reverse("teacher-gradebook--request"),
        json.dumps({"group_id": 1}),
        content_type="application/json",
    )

    assert resp.status_code == 400
    assert RunningTask.objects.count() == n


def test_request_gradebook__invalid_assignment(client, teacher, group):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)

    n = RunningTask.objects.count()

    resp = client.post(
        reverse("teacher-gradebook--request"),
        json.dumps({"group_id": group.pk, "assignment_id": 1}),
        content_type="application/json",
    )

    assert resp.status_code == 400
    assert RunningTask.objects.count() == n


def test_request_gradebook__no_teacher_access(client, teacher, group):
    assert login_teacher(client, teacher)

    n = RunningTask.objects.count()

    resp = client.post(
        reverse("teacher-gradebook--request"),
        json.dumps({"group_id": group.pk}),
        content_type="application/json",
    )

    assert resp.status_code == 403
    assert RunningTask.objects.count() == n


def test_request_gradebook__invalid_assignment(client, teacher, group):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)

    n = RunningTask.objects.count()

    resp = client.post(
        reverse("teacher-gradebook--request"),
        json.dumps({"group_id": group.pk, "assignment_id": 1}),
        content_type="application/json",
    )

    assert resp.status_code == 400
    assert RunningTask.objects.count() == n
