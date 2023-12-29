import json

import pytest
from django.urls import reverse

from functional_tests.fixtures import (  # noqa
    realistic_assignment,
    realistic_questions,
)
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher
from REST.serializers import AssignmentSerializer


@pytest.mark.django_db
def test_dynamic_serializer_querystring(client, assignments, teacher):
    """
    Test DynamicFieldsModelSerializer.

    Requirements:
    1. Return subset of specified fields in querystring
    """
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher", args=(teacher.pk,))
    response = client.get(url)

    data = json.loads(response.content)

    # Check all fields present
    fields = [
        "activeAssignmentCount",
        "activeGroupCount",
        "archived_questions",
        "assignable_groups",
        "assignment_pks",
        "assignments",
        "bookmarked_collections",
        "createdQuestionCount",
        "current_groups",
        "deleted_questions",
        "favourite_questions",
        "owned_assignments",
        "pk",
        "questions",
        "shared_questions",
        "user",
    ]
    for field in fields:
        assert field in data

    assert len(data.keys()) == len(fields)

    requested_fields = ["assignments", "pk", "fake"]
    url = f"{reverse('REST:teacher', args=(teacher.pk,))}?field={'&field='.join(requested_fields)}"  # noqa E501

    response = client.get(url)

    data = json.loads(response.content)
    for field in ["assignments", "pk"]:
        assert field in data

    assert len(data.keys()) == 2


@pytest.mark.django_db
def test_assignmentserializer_to_internal_value():
    """
    Test AssignmentSerializer to_internal_value.

    Requirements:
    1. Bleach all fields
    """
    dangerous_string = "<script><p>OK</p></script>"
    assignment = AssignmentSerializer(
        data={
            "conclusion_page": dangerous_string,
            "description": dangerous_string,
            "intro_page": dangerous_string,
            "pk": "123",
            "title": dangerous_string,
        }
    )

    assert assignment.is_valid()
    assert assignment.validated_data["title"] == "OK"
    assert assignment.validated_data["conclusion_page"] == "<p>OK</p>"
    assert assignment.validated_data["description"] == "<p>OK</p>"
    assert assignment.validated_data["intro_page"] == "<p>OK</p>"


@pytest.mark.django_db
def test_assignmentserializer_to_representation(realistic_assignment):
    """
    Test AssignmentSerializer to_representation.

    Requirements:
    1. Bleach all fields
    """
    dangerous_string = "<script><p>OK</p></script>"
    realistic_assignment.title = dangerous_string
    realistic_assignment.conclusion_page = dangerous_string
    realistic_assignment.description = dangerous_string
    realistic_assignment.intro_page = dangerous_string
    assignment = AssignmentSerializer(
        realistic_assignment,
        fields=[
            "conclusion_page",
            "description",
            "intro_page",
            "title",
        ],
    )

    assert assignment.data["title"] == "OK"
    assert assignment.data["conclusion_page"] == "<p>OK</p>"
    assert assignment.data["description"] == "<p>OK</p>"
    assert assignment.data["intro_page"] == "<p>OK</p>"
