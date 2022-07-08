import json

import pytest
from django.urls import reverse

from peerinst.models import GradingScheme
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.question import add_answers
from peerinst.tests.fixtures.teacher import login_teacher


@pytest.mark.skip(reason="Only basic view implemented")
def test_student_activity__no_questions_done(
    client,
    teacher,
    group,
    students,
    student_group_assignments,
    student_assignments,
):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)
    teacher.current_groups.add(group)

    resp = client.post(
        reverse("teacher-dashboard--student-activity"),
        json.dumps({}),
        content_type="application/json",
    )
    data = json.loads(resp.content.decode())["groups"][0]
    assert data["title"] == group.title
    assert data["n_students"] == len(students)
    assert data["new"] is True
    assert len(data["assignments"]) == len(student_group_assignments)
    for assignment, assignment_ in zip(
        data["assignments"], student_group_assignments
    ):
        assert assignment["title"] == assignment_.assignment.title
        assert assignment["n_completed"] == 0
        assert assignment["mean_grade"] == 0
        assert assignment["min_grade"] == 0
        assert assignment["max_grade"] == 0
        assert assignment["new"] is True
        assert assignment["expired"] is False
        assert assignment["link"].endswith(assignment_.hash + "/")


@pytest.mark.skip(reason="Only basic view implemented")
def test_student_activity__all_questions_done_correct_first_and_second(
    client,
    teacher,
    group,
    students,
    student_group_assignments,
    student_assignments,
):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)
    teacher.current_groups.add(group)
    for assignment in student_group_assignments:
        for question in assignment.questions:
            question.grading_scheme = GradingScheme.ADVANCED
            question.save()
        for assignment_ in assignment.studentassignment_set.all():
            add_answers(
                student=assignment_.student,
                questions=assignment.questions,
                assignment=assignment.assignment,
                correct_first=True,
                correct_second=True,
            )

    resp = client.post(
        reverse("teacher-dashboard--student-activity"),
        json.dumps({}),
        content_type="application/json",
    )
    data = json.loads(resp.content.decode())["groups"][0]
    assert data["title"] == group.title
    assert data["n_students"] == len(students)
    assert data["new"] is True
    assert len(data["assignments"]) == len(student_group_assignments)
    for assignment, assignment_ in zip(
        data["assignments"], student_group_assignments
    ):
        assert assignment["title"] == assignment_.assignment.title
        assert assignment["n_completed"] == len(assignment_.questions)
        assert assignment["mean_grade"] == len(assignment_.questions)
        assert assignment["min_grade"] == len(assignment_.questions)
        assert assignment["max_grade"] == len(assignment_.questions)
        assert assignment["new"] is True
        assert assignment["expired"] is False
        assert assignment["link"].endswith(assignment_.hash + "/")


@pytest.mark.skip(reason="Only basic view implemented")
def test_student_activity__all_questions_done_correct_first_wrong_second(
    client,
    teacher,
    group,
    students,
    student_group_assignments,
    student_assignments,
):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)
    teacher.current_groups.add(group)
    for assignment in student_group_assignments:
        for question in assignment.questions:
            question.grading_scheme = GradingScheme.ADVANCED
            question.save()
        for assignment_ in assignment.studentassignment_set.all():
            add_answers(
                student=assignment_.student,
                questions=assignment.questions,
                assignment=assignment.assignment,
                correct_first=True,
                correct_second=False,
            )

    resp = client.post(
        reverse("teacher-dashboard--student-activity"),
        json.dumps({}),
        content_type="application/json",
    )
    data = json.loads(resp.content.decode())["groups"][0]
    assert data["title"] == group.title
    assert data["n_students"] == len(students)
    assert data["new"] is True
    assert len(data["assignments"]) == len(student_group_assignments)
    for assignment, assignment_ in zip(
        data["assignments"], student_group_assignments
    ):
        assert assignment["title"] == assignment_.assignment.title
        assert assignment["n_completed"] == len(assignment_.questions)
        assert (
            assignment["mean_grade"] == float(len(assignment_.questions)) / 2
        )
        assert assignment["min_grade"] == float(len(assignment_.questions)) / 2
        assert assignment["max_grade"] == float(len(assignment_.questions)) / 2
        assert assignment["new"] is True
        assert assignment["expired"] is False
        assert assignment["link"].endswith(assignment_.hash + "/")


@pytest.mark.skip(reason="Only basic view implemented")
def test_student_activity__all_questions_done_wrong_first_and_second(
    client,
    teacher,
    group,
    students,
    student_group_assignments,
    student_assignments,
):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)
    teacher.current_groups.add(group)
    for assignment in student_group_assignments:
        for question in assignment.questions:
            question.grading_scheme = GradingScheme.ADVANCED
            question.save()
        for assignment_ in assignment.studentassignment_set.all():
            add_answers(
                student=assignment_.student,
                questions=assignment.questions,
                assignment=assignment.assignment,
                correct_first=False,
                correct_second=False,
            )

    resp = client.post(
        reverse("teacher-dashboard--student-activity"),
        json.dumps({}),
        content_type="application/json",
    )
    data = json.loads(resp.content.decode())["groups"][0]
    assert data["title"] == group.title
    assert data["n_students"] == len(students)
    assert data["new"] is True
    assert len(data["assignments"]) == len(student_group_assignments)
    for assignment, assignment_ in zip(
        data["assignments"], student_group_assignments
    ):
        assert assignment["title"] == assignment_.assignment.title
        assert assignment["n_completed"] == len(assignment_.questions)
        assert assignment["mean_grade"] == 0
        assert assignment["min_grade"] == 0
        assert assignment["max_grade"] == 0
        assert assignment["new"] is True
        assert assignment["expired"] is False
        assert assignment["link"].endswith(assignment_.hash + "/")


@pytest.mark.skip(reason="Only basic view implemented")
def test_student_activity__some_questions_done_correct_first_and_second(
    client,
    teacher,
    group,
    students,
    student_group_assignments,
    student_assignments,
):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)
    teacher.current_groups.add(group)
    for assignment in student_group_assignments:
        for question in assignment.questions:
            question.grading_scheme = GradingScheme.ADVANCED
            question.save()
        for assignment_ in assignment.studentassignment_set.all()[::2]:
            add_answers(
                student=assignment_.student,
                questions=assignment.questions,
                assignment=assignment.assignment,
                correct_first=True,
                correct_second=True,
            )

    resp = client.post(
        reverse("teacher-dashboard--student-activity"),
        json.dumps({}),
        content_type="application/json",
    )
    data = json.loads(resp.content.decode())["groups"][0]
    assert data["title"] == group.title
    assert data["n_students"] == len(students)
    assert data["new"] is True
    assert len(data["assignments"]) == len(student_group_assignments)
    for assignment, assignment_ in zip(
        data["assignments"], student_group_assignments
    ):
        assert assignment["title"] == assignment_.assignment.title
        assert assignment["n_completed"] == float(len(students[::2]))
        assert assignment["mean_grade"] == len(assignment_.questions)
        assert assignment["min_grade"] == len(assignment_.questions)
        assert assignment["max_grade"] == len(assignment_.questions)
        assert assignment["new"] is True
        assert assignment["expired"] is False
        assert assignment["link"].endswith(assignment_.hash + "/")


@pytest.mark.skip(reason="Only basic view implemented")
def test_student_activity__some_questions_done_correct_first_wrong_second(
    client,
    teacher,
    group,
    students,
    student_group_assignments,
    student_assignments,
):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)
    teacher.current_groups.add(group)
    for assignment in student_group_assignments:
        for question in assignment.questions:
            question.grading_scheme = GradingScheme.ADVANCED
            question.save()
        for assignment_ in assignment.studentassignment_set.all()[::2]:
            add_answers(
                student=assignment_.student,
                questions=assignment.questions,
                assignment=assignment.assignment,
                correct_first=True,
                correct_second=False,
            )

    resp = client.post(
        reverse("teacher-dashboard--student-activity"),
        json.dumps({}),
        content_type="application/json",
    )
    data = json.loads(resp.content.decode())["groups"][0]
    assert data["title"] == group.title
    assert data["n_students"] == len(students)
    assert data["new"] is True
    assert len(data["assignments"]) == len(student_group_assignments)
    for assignment, assignment_ in zip(
        data["assignments"], student_group_assignments
    ):
        assert assignment["title"] == assignment_.assignment.title
        assert assignment["n_completed"] == float(len(students[::2]))
        assert (
            assignment["mean_grade"] == float(len(assignment_.questions)) // 2
        )
        assert (
            assignment["min_grade"] == float(len(assignment_.questions)) // 2
        )
        assert (
            assignment["max_grade"] == float(len(assignment_.questions)) // 2
        )
        assert assignment["new"] is True
        assert assignment["expired"] is False
        assert assignment["link"].endswith(assignment_.hash + "/")


@pytest.mark.skip(reason="Only basic view implemented")
def test_student_activity__some_questions_done_wrong_first_and_second(
    client,
    teacher,
    group,
    students,
    student_group_assignments,
    student_assignments,
):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)
    teacher.current_groups.add(group)
    for assignment in student_group_assignments:
        for question in assignment.questions:
            question.grading_scheme = GradingScheme.ADVANCED
            question.save()
        for assignment_ in assignment.studentassignment_set.all()[::2]:
            add_answers(
                student=assignment_.student,
                questions=assignment.questions,
                assignment=assignment.assignment,
                correct_first=False,
                correct_second=False,
            )

    resp = client.post(
        reverse("teacher-dashboard--student-activity"),
        json.dumps({}),
        content_type="application/json",
    )
    data = json.loads(resp.content.decode())["groups"][0]
    assert data["title"] == group.title
    assert data["n_students"] == len(students)
    assert data["new"] is True
    assert len(data["assignments"]) == len(student_group_assignments)
    for assignment, assignment_ in zip(
        data["assignments"], student_group_assignments
    ):
        assert assignment["title"] == assignment_.assignment.title
        assert assignment["n_completed"] == float(len(students[::2]))
        assert assignment["mean_grade"] == 0
        assert assignment["min_grade"] == 0
        assert assignment["max_grade"] == 0
        assert assignment["new"] is True
        assert assignment["expired"] is False
        assert assignment["link"].endswith(assignment_.hash + "/")


@pytest.mark.skip(reason="Only basic view implemented")
def test_student_activity__protocol(
    client,
    settings,
    teacher,
    group,
    students,
    student_group_assignments,
    student_assignments,
):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)
    teacher.current_groups.add(group)

    resp = client.post(reverse("teacher-dashboard--student-activity"))
    data = json.loads(resp.content.decode())["groups"][0]
    for assignment in data["assignments"]:
        assert assignment["link"].startswith("http")

    settings.ALLOWED_HOSTS = ["testserver"]

    resp = client.post(reverse("teacher-dashboard--student-activity"))
    data = json.loads(resp.content.decode())["groups"][0]
    for assignment in data["assignments"]:
        assert assignment["link"].startswith("https")
