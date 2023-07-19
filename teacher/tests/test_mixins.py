import pytest
from django.urls import reverse

from peerinst.tests.fixtures import *
from peerinst.tests.fixtures.student import login_student
from peerinst.tests.fixtures.teacher import login_teacher
from tos.models import Consent, Role, Tos


@pytest.mark.django_db
def test_teacherrequiredmixin__no_anonymous_access(client):
    url = reverse("teacher:assignment-create")
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_teacherrequiredmixin__no_user_access(client, user):
    url = reverse("teacher:assignment-create")
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_teacherrequiredmixin__no_student_access(client, student):
    url = reverse("teacher:assignment-create")
    login_student(client, student)
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_teacherrequiredmixin__teacher_access(client, teacher):
    url = reverse("teacher:assignment-create")
    login_teacher(client, teacher)
    response = client.get(url)
    assert response.status_code == 200
    assert "teacher/assignment/create.html" in [
        t.name for t in response.templates
    ]


@pytest.mark.django_db
def test_teacherrequiredmixin__teacher_access_no_tos(client, teacher):
    url = reverse("teacher:assignment-create")
    login_teacher(client, teacher)
    tos = Consent.objects.get(
        user__username=teacher.user.username,
        tos__role="teacher",
    ).delete()
    response = client.get(url, follow=True)
    assert response.status_code == 200
    assert "tos/tos_modify.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_teacherrequiredmixin__teacher_access_old_tos(client, teacher):
    Tos.objects.create(
        role=Role.objects.get_or_create(role="teacher")[0],
        version=2,
        current=True,
    )

    url = reverse("teacher:assignment-create")
    login_teacher(client, teacher)
    response = client.get(url, follow=True)
    assert response.status_code == 200
    assert "tos/tos_modify.html" in [t.name for t in response.templates]
