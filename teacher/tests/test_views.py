import pytest
from django.urls import reverse
from rest_framework import status

from functional_tests.fixtures import (  # noqa
    realistic_assignment,
    realistic_questions,
)
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.student import login_student
from peerinst.tests.fixtures.teacher import login_teacher


# View access
@pytest.mark.django_db
def test_search_login_required(client, teacher):
    response = client.get(reverse("teacher:search"), follow=True)
    assert "registration/login.html" in [t.name for t in response.templates]

    response = client.get(reverse("question-search"))
    assert response.status_code == 401

    assert login_teacher(client, teacher)
    response = client.get(reverse("teacher:search"))
    assert response.status_code == 200

    response = client.get(reverse("question-search"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_search_teacher_required(client, student):
    assert login_student(client, student)
    response = client.get(reverse("teacher:search"), follow=True)
    assert response.status_code == 403

    assert login_student(client, student)
    response = client.get(reverse("question-search"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_search_template(client, teacher):
    assert login_teacher(client, teacher)
    response = client.get(reverse("teacher:search"))
    assert "teacher/search.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_teacherquestionupdateview_tos_required(client, teacher):
    pass


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
