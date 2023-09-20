import json

import pytest
from django.urls import reverse
from faker import Faker
from rest_framework import status

from functional_tests.fixtures import (  # noqa
    realistic_assignment,
    realistic_questions,
)
from peerinst.models import Answer, Question, StudentGroupAssignment
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher

fake = Faker()


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_login_required(client):
    url = reverse("REST:teacher-question-create-update-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_teacher_required(client, user):
    client.force_login(user)

    url = reverse("REST:teacher-question-create-update-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_no_list(client, teacher):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-create-update-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_no_destroy(
    client, teacher, question
):
    assert login_teacher(client, teacher)

    question.user = teacher.user
    question.save()

    url = reverse(
        "REST:teacher-question-create-update-detail", args=(question.pk,)
    )
    response = client.delete(url)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert Question.objects.filter(pk=question.pk).exists()


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_get_unowned_question(
    client, teachers, questions
):
    assert login_teacher(client, teachers[1])
    assert all(q.user != teachers[1].user for q in questions)

    url = reverse(
        "REST:teacher-question-create-update-list", args=(questions[0].pk,)
    )
    response = client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_get_owned_uneditable_question(
    client, teachers, realistic_assignment
):
    questions = realistic_assignment.questions.all()
    questions[0].user = teachers[1].user
    questions[0].save()

    assert login_teacher(client, teachers[1])
    assert questions[0].answer_set.count() > 0

    url = reverse(
        "REST:teacher-question-create-update-detail",
        args=(questions[0].pk,),
    )
    response = client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_get_owned_editable_question(
    client, teacher, question
):
    assert login_teacher(client, teacher)
    assert question.user == teacher.user
    assert question.answer_set.count() == 0

    url = reverse(
        "REST:teacher-question-create-update-detail",
        args=(question.pk,),
    )
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_get_userless_question(
    client, teacher, question
):
    assert login_teacher(client, teacher)
    assert question.answer_set.count() == 0

    question.user = None
    question.save()

    url = reverse(
        "REST:teacher-question-create-update-detail",
        args=(question.pk,),
    )
    response = client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_create_attaches_user(
    client, teacher
):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-create-update-list")
    title = fake.sentence()
    response = client.post(
        url,
        {
            "text": fake.paragraph(),
            "title": title,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Question.objects.get(title=title).user == teacher.user


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_create_text_bleached(
    client, teacher
):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-create-update-list")
    response = client.post(
        url,
        {
            "text": "<script>This is a forbidden tag</script>",
            "title": fake.sentence(),
        },
    )
    data = json.loads(response.content)

    assert response.status_code == status.HTTP_201_CREATED
    assert data["text"] == "This is a forbidden tag"


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_create_text_required(
    client, teacher
):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-create-update-list")
    response = client.post(
        url,
        {
            "text": "",
            "title": fake.sentence(),
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_create_title_bleached(
    client, teacher
):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-create-update-list")
    response = client.post(
        url,
        {
            "text": fake.paragraph(),
            "title": "<script>This is a forbidden tag</script>",
        },
    )
    data = json.loads(response.content)

    assert response.status_code == status.HTTP_201_CREATED
    assert data["title"] == "This is a forbidden tag"


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_create_title_required(
    client, teacher
):
    assert login_teacher(client, teacher)

    text = fake.paragraph()

    url = reverse("REST:teacher-question-create-update-list")
    response = client.post(
        url,
        {
            "text": text,
            "title": "",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_create_with_categories(
    client, category, teacher
):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-create-update-list")
    response = client.post(
        url,
        {
            "category_pk": [category.title],
            "text": fake.paragraph(),
            "title": fake.sentence(),
        },
    )
    data = json.loads(response.content)

    assert response.status_code == status.HTTP_201_CREATED
    assert category.title in [x["title"] for x in data["category"]]


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_create_with_discipline(
    client, discipline, teacher
):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-create-update-list")
    response = client.post(
        url,
        {
            "discipline_pk": discipline.pk,
            "text": fake.paragraph(),
            "title": fake.sentence(),
        },
    )
    data = json.loads(response.content)

    assert response.status_code == status.HTTP_201_CREATED
    assert discipline.title == data["discipline"]["title"]


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_create_with_collaborators(
    client, discipline, teachers
):
    assert login_teacher(client, teachers[0])

    url = reverse("REST:teacher-question-create-update-list")
    response = client.post(
        url,
        {
            "collaborators_pk": [
                teachers[1].user.username,
                teachers[2].user.username,
            ],
            "text": fake.paragraph(),
            "title": fake.sentence(),
        },
    )
    data = json.loads(response.content)

    assert response.status_code == status.HTTP_201_CREATED
    assert teachers[1].user.username in [
        x["username"] for x in data["collaborators"]
    ]
    assert teachers[2].user.username in [
        x["username"] for x in data["collaborators"]
    ]
