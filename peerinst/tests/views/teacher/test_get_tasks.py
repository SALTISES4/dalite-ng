import json
from unittest import mock

from django.urls import reverse

from peerinst.models import RunningTask
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher


def test_get_tasks(client, teacher):
    assert login_teacher(client, teacher)

    for i in range(1, 11):
        RunningTask.objects.create(
            id=i, description=f"test{i}", teacher=teacher
        )

    with mock.patch("peerinst.views.teacher.AsyncResult") as AsyncResult:
        result = mock.Mock()
        completed = (i % 2 == 0 for i in reversed(list(range(1, 11))))
        result.ready = lambda: next(completed)
        AsyncResult.return_value = result
        resp = client.get(reverse("teacher-tasks"))

    assert resp.status_code == 200
    data = json.loads(resp.content.decode())
    for task, i in zip(data["tasks"], reversed(list(range(1, 11)))):
        assert task["id"] == str(i)
        assert task["description"] == f"test{i}"
        assert task["completed"] == (i % 2 == 0)
