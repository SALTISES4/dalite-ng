import json
from urllib.parse import quote_plus

import pytest
from django.urls import reverse
from rest_framework import status

from peerinst.models import Assignment
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.student import login_student
from peerinst.tests.fixtures.teacher import login_teacher


@pytest.mark.django_db
def test_check_assignment_id_is_valid(client, assignment, student, teacher):
    url = reverse("REST:assignment-check-id") + f"?id={assignment.pk}"

    # Authentication required
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Teacher required
    assert login_student(client, student)

    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    assert login_teacher(client, teacher)
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK

    # GET only
    response = client.post(url, {})
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    # Return bad request if no id in query string
    response = client.get(reverse("REST:assignment-check-id"))
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Return {"valid": False} if id exists
    response = client.get(url)
    data = json.loads(response.content)

    assert not data["valid"]

    # Return {"valid": False} if id is not slug or greater than max_length
    url = (
        reverse("REST:assignment-check-id")
        + f"?id={quote_plus('123$$%^*&(*#)')}"
    )
    response = client.get(url)
    data = json.loads(response.content)

    assert not data["valid"]

    url = (
        reverse("REST:assignment-check-id")
        + "?id=11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111"  # noqa E501
    )
    response = client.get(url)
    data = json.loads(response.content)

    assert not data["valid"]


def test_get_assignment_help_texts(client, assignment, student, teacher):
    url = reverse("REST:assignment-help-texts")

    # Authentication required
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Teacher required
    assert login_student(client, student)

    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    assert login_teacher(client, teacher)
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK

    # GET only
    response = client.post(url, {})
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    # Return the help_texts
    response = client.get(url)
    data = json.loads(response.content)

    fields = [
        "intro_page",
        "conclusion_page",
        "description",
        "title",
        "identifier",
    ]
    for field in fields:
        assert field in data
        assert (
            data[field] == Assignment._meta.get_field(field).help_text.strip()
        )
