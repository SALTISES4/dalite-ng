import json

import pytest
from django.core.management import call_command
from django.urls import reverse

from functional_tests.fixtures import realistic_questions  # noqa
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.student import login_student
from peerinst.tests.fixtures.teacher import login_teacher


# View access
def test_search_login_required(client, teacher):
    response = client.get(reverse("browse-database"), follow=True)
    assert "registration/login.html" in [t.name for t in response.templates]

    response = client.get(reverse("question-search"))
    assert response.status_code == 401

    assert login_teacher(client, teacher)
    response = client.get(reverse("browse-database"))
    assert response.status_code == 200

    response = client.get(reverse("question-search"))
    assert response.status_code == 200


def test_search_teacher_required(client, student):
    assert login_student(client, student)
    response = client.get(reverse("browse-database"), follow=True)
    assert response.status_code == 403

    assert login_student(client, student)
    response = client.get(reverse("question-search"))
    assert response.status_code == 403


def test_browse_db_template(client, teacher):
    assert login_teacher(client, teacher)
    response = client.get(reverse("browse-database"))
    assert "peerinst/browse_database.html" in [
        t.name for t in response.templates
    ]


# ES-specific tests
@pytest.mark.skip(reason="Requires elasticsearch service")
def test_serialize_results(client, teacher, realistic_questions):
    call_command("search_index", "--rebuild", "-f")
    assert login_teacher(client, teacher)
    search_term = realistic_questions[0].title.split()[0]
    response = client.get(
        reverse("question-search") + "?search_string=" + search_term
    )
    data = json.loads(response.content)

    assert str(realistic_questions[0].id) in [d["id"] for d in data]
