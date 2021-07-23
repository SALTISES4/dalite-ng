import json

import mock
import pytest
from django.urls import reverse
from rest_framework import status

from peerinst.models import Assignment, AssignmentQuestions, Question
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.student import login_student
from peerinst.tests.fixtures.teacher import login_teacher


@pytest.mark.django_db
def test_dynamic_serializer_querystring(client, assignments, teacher):
    """
    Requirements:
    1. Return subset of specified fields in querystring
    """
    assert login_teacher(client, teacher)

    url = reverse("REST:teacher", args=(teacher.pk,))
    response = client.get(url)

    data = json.loads(response.content)

    # Check all fields present
    fields = [
        "archived_questions",
        "assignments",
        "deleted_questions",
        "favourite_questions",
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
def test_assignment_list(client, assignments, student, teacher):
    """
    Requirements:
    1. Must be authenticated
    2. Must be owner to GET own list
    3. Only teachers can POST to create new
    """

    # Setup
    assert teacher.user.assignment_set.exists() is False
    assignments[0].owner.add(teacher.user)

    # 1. Must be authenticated
    url = reverse("REST:assignment-list") + "?format=json"

    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # 2. Must be owner to GET own list
    assert login_teacher(client, teacher)

    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK

    retrieved_assignments = json.loads(response.content)
    assert len(retrieved_assignments) == 1
    assert retrieved_assignments[0]["title"] == assignments[0].title

    # 3. Only teachers can POST to create new assignments
    response = client.post(
        url, {"title": "<script>New assignment</script>", "pk": "UNIQUE"}
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client.get(url)
    retrieved_assignments = json.loads(response.content)
    assert len(retrieved_assignments) == 2

    created_assignment = Assignment.objects.get(pk="UNIQUE")
    assert teacher.user in created_assignment.owner.all()
    assert created_assignment in teacher.assignments.all()
    # NB: Just double check that model save() is called
    assert created_assignment.title == "New assignment"

    assert login_student(client, student)
    response = client.post(
        url, {"title": "Another new assignment", "pk": "DIFFERENT"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_assignment_detail(client, assignments, questions, teacher):
    """
    Requirements:
    1. Must be authenticated
    2. Must be owner to GET
    3. Must be owner to PATCH
    4. No one can DELETE
    5. Cannot edit is assignment.editable is false
    """

    # Setup
    assert teacher.user.assignment_set.exists() is False
    assignments[0].owner.add(teacher.user)

    # 1. Must be authenticated
    url = (
        reverse("REST:assignment-detail", args=[assignments[0].pk])
        + "?format=json"
    )

    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    assert login_teacher(client, teacher)

    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK

    # 2. Must be owner to GET
    retrieved_assignment = json.loads(response.content)
    assert retrieved_assignment["title"] == assignments[0].title
    for q in retrieved_assignment["questions"]:
        assert q["question"]["pk"] in assignments[0].questions.values_list(
            "pk", flat=True
        )

    response = client.get(
        reverse("REST:assignment-detail", args=[assignments[1].pk])
        + "?format=json"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # 3. Must be owner to PATCH and submit question list
    response = client.patch(
        url,
        {
            "title": assignments[0].title,
            "questions": retrieved_assignment["questions"],
        },
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK

    response = client.patch(
        url,
        {
            "title": assignments[0].title,
            "questions": retrieved_assignment["questions"][0:2],
        },
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.patch(
        reverse("REST:assignment-detail", args=[assignments[1].pk]),
        {
            "title": assignments[1].title,
            "questions": retrieved_assignment["questions"],
        },
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # 4. No one can DELETE
    response = client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    # 5. Cannot edit if assignment.editable is false
    with mock.patch(
        "peerinst.models.Assignment.editable", new_callable=mock.PropertyMock
    ) as mock_editable:
        mock_editable.return_value = False
        response = client.patch(
            url,
            {
                "title": assignments[0].title,
                "questions": retrieved_assignment["questions"],
            },
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.skip
def test_assignmentquestions_detail(client, assignments, student, teachers):
    """
    See also:
    - peerinst/tests/views/test_nonLTI_views.py test_assignment_update_post

    Requirements:
    1. Must be authenticated
    2. Students cannot GET
    3. Only return owned assignments
    4. Must be owner of related assignment to create or delete
    5. Cannot create or delete if assignment.editable is false
    """

    # Setup
    assignments[0].owner.add(teachers[0].user)
    assignments[1].owner.add(teachers[1].user)

    # 1. Must be authenticated
    url = reverse("REST:assignment_question-list")

    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # 2. Students cannot GET
    assert login_student(client, student)

    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # 3. Only return owned assignments
    assert login_teacher(client, teachers[0])

    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    for aq in json.loads(response.content):
        assert aq["pk"] in AssignmentQuestions.objects.filter(
            assignment=assignments[0]
        ).values_list("pk", flat=True)
        assert aq["pk"] not in AssignmentQuestions.objects.exclude(
            pk__in=assignments[0].questions.all()
        )

    # 4. Must be owner of related assignment to create or delete
    question_to_remove = AssignmentQuestions.objects.filter(
        assignment=assignments[0]
    ).first()
    question_to_add = question_to_remove.question
    url = reverse(
        "REST:assignment_question-detail", args=[question_to_remove.pk]
    )

    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assignments[0].refresh_from_db()
    assert question_to_remove.question not in assignments[0].questions.all()

    url = reverse("REST:assignment_question-list")

    response = client.post(
        url,
        {"assignment": assignments[0].pk, "question_pk": question_to_add.pk},
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_201_CREATED

    assignments[0].refresh_from_db()
    assert question_to_add in assignments[0].questions.all()

    assert login_teacher(client, teachers[1])
    question_to_remove = AssignmentQuestions.objects.filter(
        assignment=assignments[0]
    ).first()
    url = reverse(
        "REST:assignment_question-detail", args=[question_to_remove.pk]
    )

    response = client.delete(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    assignments[0].refresh_from_db()
    assert question_to_remove.question in assignments[0].questions.all()

    url = reverse("REST:assignment_question-list")

    question_to_add = Question.objects.create(
        title="question_to_add", text="text"
    )
    response = client.post(
        url,
        {"assignment": assignments[0].pk, "question_pk": question_to_add.pk},
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    assignments[0].refresh_from_db()
    assert question_to_add not in assignments[0].questions.all()

    # 5. Cannot create or delete if assignment.editable is false
    assert login_teacher(client, teachers[0])
    with mock.patch(
        "peerinst.models.Assignment.editable", new_callable=mock.PropertyMock
    ) as mock_editable:
        mock_editable.return_value = False

        question_to_remove = AssignmentQuestions.objects.filter(
            assignment=assignments[0]
        ).first()
        url = reverse(
            "REST:assignment_question-detail", args=[question_to_remove.pk]
        )

        response = client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        url = reverse("REST:assignment_question-list")
        response = client.post(
            url,
            {
                "assignment": assignments[0].pk,
                "question_pk": Question.objects.last().pk,
            },
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_discipline_list(client, disciplines, student, teacher):
    """
    Requirements:
    1. Must be authenticated
    2. Must not be a student to GET
    3. Must be admin for anything else
    """

    # 1. Must be authenticated
    url = reverse("REST:discipline-list")

    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # 2. Must not be a student to GET
    assert login_student(client, student)

    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    assert login_teacher(client, teacher)

    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    retrieved_disciplines = json.loads(response.content)
    for d in disciplines:
        assert d.pk in [d["pk"] for d in retrieved_disciplines]

    # 3. Must be admin for anything else
    response = client.post(url, {"title": "New discipline"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_teacher_questions(client, questions, teachers):
    """
    Requirements:
    1. Must be authenticated
    2. Only current teacher endpoint is accessible via GET
    3. Can update favourites through PUT
    4. Can update deleted and archived through PUT
    5. Cannot delete a question we don't own
    6. Can only archive questions we own or share
    7. No other http methods
    """

    # Setup
    teachers[0].favourite_questions.add(questions[0], questions[1])

    # 1. Must be authenticated
    url = reverse("REST:teacher", args=[teachers[0].pk])

    response = client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # 2. Only current teacher endpoint is accessible via GET
    assert login_teacher(client, teachers[0])

    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    favourites = json.loads(response.content)["favourite_questions"]
    for f in favourites:
        assert f in [fq.pk for fq in teachers[0].favourite_questions.all()]

    url = reverse("REST:teacher", args=[teachers[1].pk])

    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # 3. Can update favourites through PUT
    url = reverse("REST:teacher", args=[teachers[0].pk])

    new_favourites = [questions[0].pk, questions[2].pk]
    response = client.put(
        url,
        {"favourite_questions": new_favourites},
        content_type="application/json",
    )
    retrieved_favourites = json.loads(response.content)["favourite_questions"]

    for q in retrieved_favourites:
        assert q in new_favourites
        assert q in teachers[0].favourite_questions.values_list(
            "pk", flat=True
        )
    assert questions[1].pk not in retrieved_favourites
    assert questions[1] not in teachers[0].favourite_questions.all()

    # 4. Can update deleted_questions and archived_questions through PUT
    assert login_teacher(client, teachers[1])

    assert teachers[1].user.question_set.count() == 0
    questions[0].user = teachers[1].user
    questions[0].save()

    new_deleted = [questions[0].pk]
    new_archived = [questions[0].pk]

    url = reverse("REST:teacher", args=[teachers[1].pk])
    response = client.put(
        url,
        {"archived_questions": new_archived, "deleted_questions": new_deleted},
        content_type="application/json",
    )

    assert questions[0] in teachers[1].deleted_questions.all()
    assert questions[0] in teachers[1].archived_questions.all()
    assert response.status_code == status.HTTP_200_OK

    # 5. Cannot delete a question we don't own
    assert questions[1].user != teachers[1].user

    response = client.put(
        url,
        {
            "deleted_questions": [questions[2].pk],
        },
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # 6. Can only archive questions we own or share
    assert questions[2].user != teachers[1].user
    assert teachers[1].user not in questions[2].collaborators.all()

    response = client.put(
        url,
        {
            "archived_questions": [questions[1].pk],
        },
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    questions[3].collaborators.add(teachers[1].user)
    response = client.put(
        url,
        {
            "archived_questions": [questions[3].pk],
        },
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_200_OK

    # 7. No other http methods
    disallowed = ["post", "patch", "delete", "head", "options", "trace"]

    for method in disallowed:
        response = getattr(client, method)(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
