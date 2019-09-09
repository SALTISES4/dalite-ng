import json

from django.core.urlresolvers import reverse

from peerinst.models import RunningTask
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher


def test_remove_gradebook_task__exists(client, teacher):
    assert login_teacher(client, teacher)

    RunningTask.objects.create(id=1, description="test", teacher=teacher)

    resp = client.post(
        reverse("teacher-gradebook--remove"),
        json.dumps({"task_id": 1}),
        content_type="application/json",
    )

    assert resp.status_code == 200
    assert not RunningTask.objects.filter(id=1).exists()


def test_remove_gradebook_task__doesn_t_exists(client, teacher):
    assert login_teacher(client, teacher)

    resp = client.post(
        reverse("teacher-gradebook--remove"),
        json.dumps({"task_id": 1}),
        content_type="application/json",
    )

    assert resp.status_code == 200


def test_remove_gradebook_task__missing_params(client, teacher):
    assert login_teacher(client, teacher)

    resp = client.post(
        reverse("teacher-gradebook--remove"),
        json.dumps({}),
        content_type="application/json",
    )

    assert resp.status_code == 400
