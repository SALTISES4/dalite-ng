import json

import mock
from django.http import HttpResponse
from django.urls import reverse

from peerinst.models import Assignment, Collection
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.student import login_student
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
    data = json.loads(resp.content.decode())
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
    data = json.loads(resp.content.decode())
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


# Collection copy workflow
def test_collections__copy_access(client, collection, student, teacher):
    # 1. url name collection-copy at collection/copy
    url = reverse("collection-copy")
    assert "collection/copy" in url

    # 2. Require POST
    response = client.get(url)
    assert response.status_code == 405

    # 3. Must be authenticated
    response = client.post(url, {}, follow=True)
    assert "registration/login.html" in [t.name for t in response.templates]

    # 4. Must be a teacher
    assert login_student(client, student)
    response = client.post(url, {})
    assert "/access_denied_and_logout/" in response.url

    # 5. Requires pk
    assert login_teacher(client, teacher)
    response = client.post(url, {})
    assert response.status_code == 400

    response = client.post(url, {"pk": collection.pk}, follow=True)
    assert response.status_code == 200

    # 6. Requires not private
    collection.private = True
    collection.save()

    response = client.post(url, {"pk": collection.pk}, follow=True)
    assert response.status_code == 400


def test_collections__copy(client, collections, teacher):
    url = reverse("collection-copy")

    assert login_teacher(client, teacher)
    collection_count = Collection.objects.count()
    collection_to_copy = collections[3]
    assignment_count = Assignment.objects.count()

    response = client.post(url, {"pk": collection_to_copy.pk})

    # 1. New collection created
    assert Collection.objects.count() == collection_count + 1
    new_collection = Collection.objects.last()

    # 2. Each assignment in collection_to_copy is copied with parent set
    assert (
        Assignment.objects.count()
        == assignment_count + collection_to_copy.assignments.count()
    )
    assert set(a.parent for a in new_collection.assignments.all()) == set(
        collection_to_copy.assignments.all()
    )

    # 3. Owner of each new assignment is current user
    for assignment in new_collection.assignments.all():
        assert teacher.user in assignment.owner.all()

    # 4. Redirect should be to collection detail view
    assert "peerinst/collection/collection_detail.html" in [
        t.name for t in response.templates
    ]
