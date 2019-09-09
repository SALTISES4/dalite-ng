import json

from django.core.urlresolvers import reverse
from pinax.forums.models import ThreadSubscription

from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher


def test_unsubscribe_from_thread(client, teacher, thread):
    assert login_teacher(client, teacher)
    assert ThreadSubscription.objects.filter(
        user=teacher.user, thread=thread
    ).count()

    resp = client.post(
        reverse("teacher-dashboard--unsubscribe-thread"),
        json.dumps({"id": thread.pk}),
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert not ThreadSubscription.objects.filter(
        user=teacher.user, thread=thread
    ).count()


def test_unsubscribe_from_thread__missing_params(client, teacher, thread):
    assert login_teacher(client, teacher)
    assert ThreadSubscription.objects.filter(
        user=teacher.user, thread=thread
    ).count()

    resp = client.post(
        reverse("teacher-dashboard--unsubscribe-thread"),
        json.dumps({}),
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert ThreadSubscription.objects.filter(
        user=teacher.user, thread=thread
    ).count()


def test_unsubscribe_from_thread__wrong_thread(client, teacher):
    assert login_teacher(client, teacher)

    resp = client.post(
        reverse("teacher-dashboard--unsubscribe-thread"),
        json.dumps({"id": 1}),
        content_type="application/json",
    )
    assert resp.status_code == 400
