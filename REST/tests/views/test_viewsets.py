import pytest
from django.urls import reverse
from faker import Faker
from rest_framework import status

from peerinst.models import Question
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher

fake = Faker()


@pytest.mark.django_db
def test_teachercreateupdateviewset_login_required(client):
    url = reverse("REST:teacher-question-create-update-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_teachercreateupdateviewset_teacher_required(client, user):
    client.force_login(user)

    url = reverse("REST:teacher-question-create-update-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_teachercreateupdateviewset_no_list(client, teacher):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-create-update-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_teachercreateupdateviewset_no_PUT(client, teacher, question):
    assert login_teacher(client, teacher)

    question.user = teacher.user
    question.save()

    url = reverse(
        "REST:teacher-question-create-update-detail", args=(question.pk,)
    )
    text = fake.paragraph()
    response = client.put(
        url,
        data={
            "text": text,
        },
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    question.refresh_from_db()
    assert question.text != text
