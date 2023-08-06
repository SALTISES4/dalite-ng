import json

import pytest
from django.urls import reverse
from faker import Faker
from rest_framework import status

from peerinst.models import Question, StudentGroupAssignment
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher

fake = Faker()


@pytest.mark.django_db
def test_feedback_duplication(client, teacher, answers):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-feedback-list")
    response = client.post(url, {"score": 1, "answer": answers[0].pk})
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post(url, {"score": 1, "answer": answers[0].pk})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_studentgroupassignmentviewset_login_required(client):
    url = reverse("REST:studentgroupassignment-list")
    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_studentgroupassignmentviewset_teacher_required(client, user):
    client.force_login(user)

    url = reverse("REST:studentgroupassignment-list")
    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_studentgroupassignmentviewset_queryset(
    client, teacher, student_group_assignments
):
    assert login_teacher(client, teacher)

    # Empty response if teacher has no groups
    url = reverse("REST:studentgroupassignment-list")
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 0

    # Only studentgroupassignments attached to teacher's groups
    student_group_assignments[0].group.teacher.add(teacher)
    url = reverse("REST:studentgroupassignment-list")
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = json.loads(response.content)
    for obj in data:
        assert (
            teacher
            in StudentGroupAssignment.objects.get(
                pk=obj["pk"]
            ).group.teacher.all()
        )


@pytest.mark.django_db
def test_teacherquestionviewset_login_required(client):
    url = reverse("REST:teacher-question-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_teacherquestionviewset_queryset(client, teachers, questions):
    assert login_teacher(client, teachers[1])
    assert all(q.user != teachers[1].user for q in questions)

    url = reverse("REST:teacher-question-list")
    response = client.get(url)
    data = json.loads(response.content)

    assert response.status_code == status.HTTP_200_OK
    assert len(data) == 0

    questions[0].user = teachers[1].user
    questions[0].save()
    response = client.get(url)
    data = json.loads(response.content)

    assert len(data) == 1
    assert data[0]["pk"] == questions[0].pk


@pytest.mark.django_db
def test_teacherquestionviewset_create_attaches_user(client, teacher):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-list")
    response = client.post(
        url,
        {
            "text": fake.paragraph(),
            "title": fake.sentence(),
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Question.objects.get(title=title).user == teacher.user


@pytest.mark.django_db
def test_teacherquestionviewset_create_text_bleached(client, teacher):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-list")
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
def test_teacherquestionviewset_create_text_required(client, teacher):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-list")
    response = client.post(
        url,
        {
            "text": "",
            "title": fake.sentence(),
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_teacherquestionviewset_create_title_bleached(client, teacher):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-list")
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
def test_teacherquestionviewset_create_title_required(client, teacher):
    assert login_teacher(client, teacher)

    text = fake.paragraph()

    url = reverse("REST:teacher-question-list")
    response = client.post(
        url,
        {
            "text": text,
            "title": "",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
