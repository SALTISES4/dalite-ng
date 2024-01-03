import json

import pytest
from django.urls import reverse

from functional_tests.fixtures import (  # noqa
    realistic_assignment,
    realistic_questions,
)
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher
from REST.serializers import AssignmentSerializer, QuestionSerializer


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


@pytest.mark.django_db
def test_questionserializer_create_set_pk():
    """
    Test QuestionSerializer create method.

    Requirement:
    1. pk cannot be set
    """
    question_serializer = QuestionSerializer(
        data={
            "title": "Question title",
            "text": "Question text",
            "type": "RO",
            "pk": 4,
        }
    )
    assert question_serializer.is_valid()
    assert "pk" not in question_serializer.validated_data
    question = question_serializer.save()
    assert question.pk != 4


@pytest.mark.django_db
def test_questionserializer_create_set_parent(realistic_questions):
    """
    Test QuestionSerializer create method.

    Requirement:
    1. `parent` should be set if valid pk passed
    2. If invalid pk passed, raise error
    3. If nothing passed, set None
    """
    question_serializer = QuestionSerializer(
        data={
            "title": "Question title",
            "text": "Question text",
            "type": "RO",
            "parent": realistic_questions[0].pk,
        }
    )
    assert question_serializer.is_valid()
    question = question_serializer.save()
    assert question.parent.pk == realistic_questions[0].pk

    question_serializer = QuestionSerializer(
        data={
            "title": "Another question title",
            "text": "Question text",
            "type": "RO",
            "parent": 1000000000000,
        }
    )
    question_serializer.is_valid()
    assert question_serializer.errors["parent"][0].code == "does_not_exist"

    question_serializer = QuestionSerializer(
        data={
            "title": "Another question title",
            "text": "Question text",
            "type": "RO",
        }
    )
    question_serializer.is_valid()
    question = question_serializer.save()
    assert question.parent is None


@pytest.mark.django_db
def test_questionserializer_create_RO():
    """
    Test QuestionSerializer create method.

    Requirement:
    1. RO must have second_answer_needed as False
    """
    question_serializer = QuestionSerializer(
        data={
            "title": "Question title",
            "text": "Question text",
            "second_answer_needed": True,
            "type": "RO",
        }
    )
    assert question_serializer.is_valid()
    question = question_serializer.save()
    assert not question.second_answer_needed


@pytest.mark.django_db
def test_questionserializer_update_no_pk():
    """
    Test QuestionSerializer update method.

    Requirement:
    1. pk cannot be changed
    """
    question_serializer = QuestionSerializer(
        data={
            "title": "Question title",
            "text": "Question text",
            "type": "RO",
        }
    )
    assert question_serializer.is_valid()
    question = question_serializer.save()

    update_serializer = QuestionSerializer(
        instance=question,
        partial=True,
        data={"title": "New question title", "pk": 4},
    )
    assert update_serializer.is_valid()
    assert "pk" not in update_serializer.validated_data
    update_serializer.save()
    question.refresh_from_db()
    assert question.title == "New question title"
    assert question.pk != 4


@pytest.mark.django_db
def test_questionserializer_update_parent(realistic_questions):
    """
    Test QuestionSerializer update method.

    Requirement:
    1. parent cannot be changed
    """
    question_serializer = QuestionSerializer(
        data={
            "title": "Question title",
            "text": "Question text",
            "type": "RO",
            "parent": realistic_questions[0].pk,
        }
    )
    assert question_serializer.is_valid()
    question = question_serializer.save()

    update_serializer = QuestionSerializer(
        instance=question,
        partial=True,
        data={
            "parent": realistic_questions[1].pk,
        },
    )
    assert update_serializer.is_valid()
    update_serializer.save()
    question.refresh_from_db()
    assert question.parent.pk == realistic_questions[0].pk
