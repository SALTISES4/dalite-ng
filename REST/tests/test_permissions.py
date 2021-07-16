import pytest
from django.urls import reverse
from rest_framework import status

from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.student import login_student
from peerinst.tests.fixtures.teacher import login_teacher
from REST.permissions import InTeacherList, IsNotStudent


@pytest.mark.django_db
def test_is_not_student_permission(client, rf, student, teacher):

    rf.user = student.student

    assert not IsNotStudent().has_permission(rf, None)

    rf.user = teacher.user

    assert IsNotStudent().has_permission(rf, None)


@pytest.mark.django_db
def test_is_not_student_permission_in_view(
    client, student, student_group_assignment
):

    assert login_student(client, student)

    url = reverse(
        "REST:student-group-assigment-answers",
        args=[
            student_group_assignment.pk,
            student_group_assignment.assignment.questions.first().pk,
        ],
    )

    response = client.get(url)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_in_teacher_list_permission(
    client, rf, student_group_assignment, teacher
):

    rf.user = teacher.user

    assert not InTeacherList().has_object_permission(
        rf, None, student_group_assignment
    )

    student_group_assignment.group.teacher.add(teacher)

    assert InTeacherList().has_object_permission(
        rf, None, student_group_assignment
    )

    assert InTeacherList().has_object_permission(
        rf, None, student_group_assignment.group
    )

    with pytest.raises(AttributeError):
        assert InTeacherList().has_object_permission(
            rf, None, student_group_assignment.group.group
        )


@pytest.mark.django_db
def test_in_teacher_list_permission_in_view(
    client, student_group_assignment, teacher
):
    assert teacher not in student_group_assignment.group.teacher.all()

    assert login_teacher(client, teacher)

    url = reverse(
        "REST:student-group-assigment-answers",
        args=[
            student_group_assignment.pk,
            student_group_assignment.assignment.questions.first().pk,
        ],
    )

    response = client.get(url)

    # 404 based on limited queryset
    assert response.status_code == status.HTTP_404_NOT_FOUND

    student_group_assignment.group.teacher.add(teacher)

    assert teacher in student_group_assignment.group.teacher.all()

    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
