import pytest
from django.urls import reverse
from rest_framework import status

from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher


@pytest.mark.django_db
def test_feedback_duplication(client, teacher, answers):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-feedback-list")
    response = client.post(url, {"score": 1, "answer": answers[0].pk})
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post(url, {"score": 1, "answer": answers[0].pk})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
