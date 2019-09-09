import json

import mock
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher


def test_collections(client, collections, teachers, discipline):
    teacher = teachers[0]
    teachers = teachers[1:]

    teacher.disciplines.add(discipline)

    assert login_teacher(client, teacher)

    for i, collection in enumerate(collections):
        collection.followers.remove(*teachers[: -i - 1])

    resp = client.post(
        reverse("teacher-dashboard--collections"),
        json.dumps({}),
        content_type="application/json",
    )

    assert resp.status_code == 200
    data = json.loads(resp.content)
    assert len(data["collections"]) == len(collections)

    for collection, collection_ in zip(
        data["collections"], reversed(collections)
    ):
        assert collection["title"] == collection_.title
        assert collection["description"] == collection_.description
        assert collection["discipline"] == collection_.discipline.title
        assert collection["n_assignments"] == collection_.assignments.count()
        assert collection["n_followers"] == collection_.followers.count()


def test_collections__with_params(client, collections, teachers, discipline):
    teacher = teachers[0]
    teachers = teachers[1:]

    teacher.disciplines.add(discipline)

    assert login_teacher(client, teacher)

    for i, collection in enumerate(collections):
        collection.followers.remove(*teachers[: -i - 1])

    resp = client.post(
        reverse("teacher-dashboard--collections"),
        json.dumps({"n": 1}),
        content_type="application/json",
    )

    assert resp.status_code == 200
    data = json.loads(resp.content)
    assert len(data["collections"]) == 1

    for collection, collection_ in zip(
        data["collections"], reversed(collections)
    ):
        assert collection["title"] == collection_.title
        assert collection["description"] == collection_.description
        assert collection["discipline"] == collection_.discipline.title
        assert collection["n_assignments"] == collection_.assignments.count()
        assert collection["n_followers"] == collection_.followers.count()


def test_collections__wrong_params(client, teacher):
    assert login_teacher(client, teacher)

    with mock.patch(
        "peerinst.views.teacher.get_json_params",
        return_value=HttpResponse("", status=400),
    ):
        resp = client.post(
            reverse("teacher-dashboard--collections"),
            json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400
