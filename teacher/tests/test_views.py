import pytest
from django.urls import reverse
from faker import Faker
from rest_framework import status

from functional_tests.fixtures import realistic_assignment, realistic_questions
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher

fake = Faker()


@pytest.mark.django_db
def test_teacherquestionupdateview_retrieve_unowned_question(
    client, teachers, questions
):
    assert login_teacher(client, teachers[1])
    assert all(q.user != teachers[1].user for q in questions)

    url = reverse("teacher:question-update", args=(questions[0].pk,))
    response = client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_teacherquestionupdateview_retrieve_owned_uneditable_question(
    client, teachers, realistic_assignment
):
    questions = realistic_assignment.questions.all()
    questions[0].user = teachers[1].user
    questions[0].save()

    assert login_teacher(client, teachers[1])
    assert questions[0].answer_set.count() > 0

    url = reverse(
        "teacher:question-update",
        args=(questions[0].pk,),
    )
    response = client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_teacherquestionupdateview_retrieve_owned_editable_question(
    client, teacher, question
):
    assert login_teacher(client, teacher)
    assert question.user == teacher.user
    assert question.answer_set.count() == 0

    url = reverse(
        "teacher:question-update",
        args=(question.pk,),
    )
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_teacherquestionupdateview_retrieve_userless_question(
    client, teacher, question
):
    assert login_teacher(client, teacher)
    assert question.answer_set.count() == 0

    question.user = None
    question.save()

    url = reverse(
        "teacher:question-update",
        args=(question.pk,),
    )
    response = client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
