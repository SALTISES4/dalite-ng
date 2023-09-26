import json
import os

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from faker import Faker
from rest_framework import status

from functional_tests.fixtures import (  # noqa
    realistic_assignment,
    realistic_questions,
)
from peerinst.models import Question
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.teacher import login_teacher

fake = Faker()


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_retrieve_unowned_question(
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
def test_teacherquestioncreateupdateviewset_retrieve_owned_uneditable_question(
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
def test_teacherquestioncreateupdateviewset_retrieve_owned_editable_question(
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
def test_teacherquestioncreateupdateviewset_retrieve_userless_question(
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
        data={
            "text": fake.paragraph(),
            "title": title,
            "answerchoice_set": [
                {"correct": True, "text": fake.sentence()},
            ],
        },
        content_type="application/json",
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
        data={
            "text": "<script>This is a forbidden tag</script>",
            "title": fake.sentence(),
            "answerchoice_set": [
                {"correct": True, "text": fake.sentence()},
            ],
        },
        content_type="application/json",
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
        data={
            "text": "",
            "title": fake.sentence(),
            "answerchoice_set": [
                {"correct": True, "text": fake.sentence()},
            ],
        },
        content_type="application/json",
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
        data={
            "text": fake.paragraph(),
            "title": "<script>This is a forbidden tag</script>",
            "answerchoice_set": [
                {"correct": True, "text": fake.sentence()},
            ],
        },
        content_type="application/json",
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
        data={
            "text": text,
            "title": "",
            "answerchoice_set": [
                {"correct": True, "text": fake.sentence()},
            ],
        },
        content_type="application/json",
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
        data={
            "category_pk": [category.title],
            "text": fake.paragraph(),
            "title": fake.sentence(),
            "answerchoice_set": [
                {"correct": True, "text": fake.sentence()},
            ],
        },
        content_type="application/json",
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
        data={
            "discipline_pk": discipline.pk,
            "text": fake.paragraph(),
            "title": fake.sentence(),
            "answerchoice_set": [
                {"correct": True, "text": fake.sentence()},
            ],
        },
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert discipline.title == response.data["discipline"]["title"]


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_create_with_collaborators(
    client, discipline, teachers
):
    assert login_teacher(client, teachers[0])

    url = reverse("REST:teacher-question-create-update-list")
    response = client.post(
        url,
        data={
            "collaborators_pk": [
                teachers[1].user.username,
                teachers[2].user.username,
            ],
            "text": fake.paragraph(),
            "title": fake.sentence(),
            "answerchoice_set": [
                {"correct": True, "text": fake.sentence()},
            ],
        },
        content_type="application/json",
    )
    data = json.loads(response.content)

    assert response.status_code == status.HTTP_201_CREATED
    assert teachers[1].user.username in [
        x["username"] for x in data["collaborators"]
    ]
    assert teachers[2].user.username in [
        x["username"] for x in data["collaborators"]
    ]


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_create_image_png(client, teacher):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-create-update-list")
    response = client.post(
        url,
        data={
            "text": fake.paragraph(),
            "title": fake.sentence(),
            "image": SimpleUploadedFile(
                name="sample-file.jpg",
                content=open(
                    os.path.join(
                        settings.BASE_DIR,
                        "peerinst/static/peerinst/img/SALTISE-badge.png",
                    ),
                    "rb",
                ).read(),
            ),
            "answerchoice_set[0]correct": True,
            "answerchoice_set[0]text": fake.sentence(),
        },
    )

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_create_image_svg(client, teacher):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-create-update-list")
    response = client.post(
        url,
        data={
            "text": fake.paragraph(),
            "title": fake.sentence(),
            "image": SimpleUploadedFile(
                name="sample-file.jpg",
                content=open(
                    os.path.join(
                        settings.BASE_DIR,
                        "peerinst/static/peerinst/img/thumbs-up.svg",
                    ),
                    "rb",
                ).read(),
            ),
            "answerchoice_set[0]correct": True,
            "answerchoice_set[0]text": fake.sentence(),
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_create_image_large_file(
    client, teacher
):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-create-update-list")
    response = client.post(
        url,
        data={
            "text": fake.paragraph(),
            "title": fake.sentence(),
            "image": SimpleUploadedFile(
                name="sample-file.jpg",
                content=open(
                    os.path.join(
                        settings.BASE_DIR,
                        "peerinst/static/peerinst/img/ray-hennessy-gdTxVSAE5sk-unsplash.jpg",
                    ),
                    "rb",
                ).read(),
            ),
            "answerchoice_set[0]correct": True,
            "answerchoice_set[0]text": fake.sentence(),
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_update_owned_editable_question(
    client, teacher, question
):
    assert login_teacher(client, teacher)
    assert question.user == teacher.user
    assert question.answer_set.count() == 0

    url = reverse(
        "REST:teacher-question-create-update-detail",
        args=(question.pk,),
    )
    text = fake.paragraph()
    title = fake.sentence()
    response = client.patch(
        url,
        data={
            "text": text,
            "title": title,
        },
        content_type="application/json",
    )

    assert response.status_code == status.HTTP_200_OK
    question.refresh_from_db()
    assert question.text == text
    assert question.title == title


@pytest.mark.django_db
def test_teacherquestioncreateupdateviewset_create_answerchoices_none_correct(
    client, teacher
):
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher-question-create-update-list")

    response = client.post(
        url,
        data={
            "text": fake.paragraph(),
            "title": fake.sentence(),
            "answerchoice_set": [
                {"correct": False, "text": fake.sentence()},
            ],
        },
        content_type="application/json",
    )

    assert (
        "At least one answer choice must be correct"
        in response.data["answerchoice_set"]
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
