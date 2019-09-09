import json

import mock
from django.core.urlresolvers import reverse

from peerinst.models import RunningTask
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher


def test_get_tasks(client, teacher):
    assert login_teacher(client, teacher)

    for i in range(1, 11):
        RunningTask.objects.create(
            id=i, description="test{}".format(i), teacher=teacher
        )

    with mock.patch("peerinst.views.teacher.AsyncResult") as AsyncResult:
        result = mock.Mock()
        completed = (i % 2 == 0 for i in reversed(range(1, 11)))
        result.ready = lambda: next(completed)
        AsyncResult.return_value = result
        resp = client.get(reverse("teacher-tasks"))

    assert resp.status_code == 200
    data = json.loads(resp.content)
    for task, i in zip(data["tasks"], reversed(range(1, 11))):
        assert task["id"] == str(i)
        assert task["description"] == "test{}".format(i)
        assert task["completed"] == (i % 2 == 0)
