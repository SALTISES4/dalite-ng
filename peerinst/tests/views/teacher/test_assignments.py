from django.urls import reverse

from peerinst.models import Assignment
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher


def test_clone_assignment(client, assignment, teacher):
    assert login_teacher(client, teacher)

    resp = client.post(
        reverse("assignment-copy", args=[assignment.pk]),
        {
            "identifier": "unique",
            "title": "title",
            "description": "a bucket of my questions",
        },
        follow=True,
    )

    assert resp.status_code == 200

    new_assignment = Assignment.objects.last()

    for q in new_assignment.questions.all():
        assert q in assignment.questions.all()

    assert new_assignment.questions.count() == assignment.questions.count()
    assert new_assignment.parent == assignment
