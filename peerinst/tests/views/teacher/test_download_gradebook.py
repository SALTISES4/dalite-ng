import json

import mock
from django.core.urlresolvers import reverse
from django.http import StreamingHttpResponse

from peerinst.models import RunningTask
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher
from peerinst.views.teacher import download_gradebook


def test_download_gradebook__with_results__group(rf, teacher):
    req = rf.post("/test")
    req.user = teacher.user
    results = {"group": "test"}

    with mock.patch(
        "peerinst.views.teacher.convert_gradebook_to_csv"
    ) as convert_gradebook_to_csv:
        convert_gradebook_to_csv.return_value = iter(["test\n"])

        resp = download_gradebook(req, results=results)

        assert resp.status_code == 200
        assert isinstance(resp, StreamingHttpResponse)
        assert (
            next(resp.streaming_content).strip()
            == "myDALITE_gradebook_test.csv"
        )
        assert next(resp.streaming_content).strip() == "test"


def test_download_gradebook__with_results__assignment(rf, teacher):
    req = rf.post("/test")
    req.user = teacher.user
    results = {"group": "test", "assignment": "test"}

    with mock.patch(
        "peerinst.views.teacher.convert_gradebook_to_csv"
    ) as convert_gradebook_to_csv:
        convert_gradebook_to_csv.return_value = iter(["test\n"])

        resp = download_gradebook(req, results=results)

        assert resp.status_code == 200
        assert isinstance(resp, StreamingHttpResponse)
        assert (
            next(resp.streaming_content).strip()
            == "myDALITE_gradebook_test_test.csv"
        )
        assert next(resp.streaming_content).strip() == "test"


def test_download_gradebook__group(client, teacher):
    assert login_teacher(client, teacher)

    RunningTask.objects.create(id=1, description="test", teacher=teacher)

    with mock.patch(
        "peerinst.views.teacher.convert_gradebook_to_csv"
    ) as convert_gradebook_to_csv, mock.patch(
        "peerinst.views.teacher.AsyncResult"
    ) as AsyncResult:
        convert_gradebook_to_csv.return_value = iter(["test\n"])
        result = mock.Mock()
        result.ready.return_value = True
        result.result = {"group": "test"}
        AsyncResult.return_value = result

        resp = client.post(
            reverse("teacher-gradebook--download"),
            json.dumps({"task_id": 1}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        assert isinstance(resp, StreamingHttpResponse)
        assert (
            next(resp.streaming_content).strip()
            == "myDALITE_gradebook_test.csv"
        )
        assert next(resp.streaming_content).strip() == "test"
        assert not RunningTask.objects.filter(id=1).exists()


def test_download_gradebook__assignment(client, teacher):
    assert login_teacher(client, teacher)

    RunningTask.objects.create(id=1, description="test", teacher=teacher)

    with mock.patch(
        "peerinst.views.teacher.convert_gradebook_to_csv"
    ) as convert_gradebook_to_csv, mock.patch(
        "peerinst.views.teacher.AsyncResult"
    ) as AsyncResult:
        convert_gradebook_to_csv.return_value = iter(["test\n"])
        result = mock.Mock()
        result.ready.return_value = True
        result.result = {"group": "test", "assignment": "test"}
        AsyncResult.return_value = result

        resp = client.post(
            reverse("teacher-gradebook--download"),
            json.dumps({"task_id": 1}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        assert isinstance(resp, StreamingHttpResponse)
        assert (
            next(resp.streaming_content).strip()
            == "myDALITE_gradebook_test_test.csv"
        )
        assert next(resp.streaming_content).strip() == "test"
        assert not RunningTask.objects.filter(id=1).exists()


def test_download_gradebook__missing_params(client, teacher):
    assert login_teacher(client, teacher)

    resp = client.post(
        reverse("teacher-gradebook--download"),
        json.dumps({}),
        content_type="application/json",
    )

    assert resp.status_code == 400


def test_download_gradebook__not_ready(client, teacher):
    assert login_teacher(client, teacher)

    RunningTask.objects.create(id=1, description="test", teacher=teacher)

    with mock.patch(
        "peerinst.views.teacher.convert_gradebook_to_csv"
    ) as convert_gradebook_to_csv, mock.patch(
        "peerinst.views.teacher.AsyncResult"
    ) as AsyncResult:
        convert_gradebook_to_csv.return_value = iter(["test\n"])
        result = mock.Mock()
        result.ready.return_value = False
        AsyncResult.return_value = result

        resp = client.post(
            reverse("teacher-gradebook--download"),
            json.dumps({"task_id": 1}),
            content_type="application/json",
        )

        assert resp.status_code == 400
        assert RunningTask.objects.filter(id=1).exists()


def test_download_gradebook__celery_error(client, teacher):
    assert login_teacher(client, teacher)

    RunningTask.objects.create(id=1, description="test", teacher=teacher)

    with mock.patch(
        "peerinst.views.teacher.convert_gradebook_to_csv"
    ) as convert_gradebook_to_csv, mock.patch(
        "peerinst.views.teacher.AsyncResult"
    ) as AsyncResult:
        convert_gradebook_to_csv.return_value = iter(["test\n"])
        result = mock.Mock()
        result.ready.side_effect = AttributeError()
        AsyncResult.return_value = result

        resp = client.post(
            reverse("teacher-gradebook--download"),
            json.dumps({"task_id": 1}),
            content_type="application/json",
        )

        assert resp.status_code == 500
        assert RunningTask.objects.filter(id=1).exists()


def test_download_gradebook__no_running_task(client, teacher):
    assert login_teacher(client, teacher)

    with mock.patch(
        "peerinst.views.teacher.convert_gradebook_to_csv"
    ) as convert_gradebook_to_csv, mock.patch(
        "peerinst.views.teacher.AsyncResult"
    ) as AsyncResult:
        convert_gradebook_to_csv.return_value = iter(["test\n"])
        result = mock.Mock()
        result.ready.return_value = True
        result.result = {"group": "test"}
        AsyncResult.return_value = result

        resp = client.post(
            reverse("teacher-gradebook--download"),
            json.dumps({"task_id": 1}),
            content_type="application/json",
        )

        assert resp.status_code == 200
        assert isinstance(resp, StreamingHttpResponse)
        assert (
            next(resp.streaming_content).strip()
            == "myDALITE_gradebook_test.csv"
        )
        assert next(resp.streaming_content).strip() == "test"
