from django.core.urlresolvers import reverse

from peerinst.models import AnswerAnnotation
from peerinst.tests.fixtures import *  # noqa
from peerinst.tests.fixtures.question.utils import add_answers
from peerinst.tests.fixtures.teacher import login_teacher


def test_student_activity__dashboard(
    client, teacher, group, questions, student, student_group_assignments
):
    assert login_teacher(client, teacher)
    group.teacher.add(teacher)
    teacher.current_groups.add(group)
    student.groups.add(group)

    add_answers(
        student,
        questions,
        student_group_assignments[0].assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )

    resp = client.get(reverse("teacher-dashboard"))

    assert resp.status_code == 200
    assert any(
        t.name == "peerinst/teacher/cards/student_activity_card.html"
        for t in resp.templates
    )
    assert any(
        t.name == "peerinst/teacher/dashboard.html" for t in resp.templates
    )
    assert str(student_group_assignments[0].assignment.title) in resp.content
    assert str(group.title) in resp.content
    assert (
        str(student_group_assignments[1].assignment.title) not in resp.content
    )


def test_new_questions__dashboard(
    client, teacher, questions, assignment, disciplines
):
    assert login_teacher(client, teacher)

    for question in questions[: len(questions) // 2]:
        question.discipline = disciplines[0]
        question.save()
    for question in questions[len(questions) // 2 :]:
        question.discipline = disciplines[1]
        question.save()

    teacher.disciplines.add(disciplines[0])

    resp = client.get(reverse("teacher-dashboard--new-questions"))

    assert resp.status_code == 200
    assert any(
        t.name == "peerinst/question/cards/question_card.html"
        for t in resp.templates
    )
    assert str(disciplines[0]) in resp.content
    assert str(disciplines[1]) not in resp.content

    # TODO: Add tests to validate choose_questions logic
    # E.g. no questions from teacher assignments, no favourites etc.


def test_rationales__dashboard(client, teacher, discipline, answers):
    assert login_teacher(client, teacher)

    teacher.disciplines.add(discipline)
    for i, answer in enumerate(answers):
        answer.question.discipline = discipline
        answer.question.save()
        answer.second_answer_choice = 1
        answer.save()

    n = AnswerAnnotation.objects.count()

    resp = client.get(reverse("teacher-dashboard--rationales"))

    assert resp.status_code == 200
    assert any(
        t.name == "peerinst/teacher/cards/rationale_to_score_card.html"
        for t in resp.templates
    )

    resp = client.post(
        reverse("teacher-dashboard--evaluate-rationale"),
        {"id": answers[0].id, "score": 0},
        follow=True,
    )

    assert resp.status_code == 200
    assert any(
        t.name == "peerinst/teacher/cards/rationale_to_score_card.html"
        for t in resp.templates
    )
    assert AnswerAnnotation.objects.count() == n + 1
