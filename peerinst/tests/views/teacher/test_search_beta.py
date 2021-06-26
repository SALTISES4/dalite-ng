from django.urls import reverse

from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.student import login_student
from peerinst.tests.fixtures.teacher import login_teacher


def test_search_login_required(client, teacher):
    response = client.get(reverse("browse-database-beta"), follow=True)
    assert "registration/login.html" in [t.name for t in response.templates]

    assert login_teacher(client, teacher)
    response = client.get(reverse("browse-database-beta"))
    assert response.status_code == 200


def test_search_teacher_required(client, student, teacher):
    assert login_student(client, student)
    response = client.get(reverse("browse-database-beta"), follow=True)
    assert response.status_code == 403


def test_search_template(client, teacher):
    assert login_teacher(client, teacher)
    response = client.get(reverse("browse-database-beta"))
    assert "peerinst/browse_database_beta.html" in [
        t.name for t in response.templates
    ]
