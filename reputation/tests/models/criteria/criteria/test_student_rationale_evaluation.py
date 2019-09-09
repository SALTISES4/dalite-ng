# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from peerinst.models import AnswerAnnotation
from peerinst.tests.fixtures import *  # noqa
from reputation.models import ReputationType
from reputation.tests.fixtures import *  # noqa


def test_dict(student_rationale_evaluation_criterion):
    data = dict(student_rationale_evaluation_criterion)
    assert len(data) == 8
    assert "version" in data
    assert "points_per_threshold" in data
    assert "thresholds" in data
    assert "badge_thresholds" in data
    assert "badge_colour" in data
    assert "name" in data
    assert "full_name" in data
    assert "description" in data


def test_evaluate__all_never_show(
    student_rationale_evaluation_criterion, student, answers, teacher
):
    for answer in answers:
        answer.user_token = student.student.username
        answer.save()
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=0
        )
    assert student_rationale_evaluation_criterion.evaluate(student)[0] == -len(
        answers
    )


def test_evaluate__all_convincing(
    student_rationale_evaluation_criterion, student, answers, teacher
):
    for i, answer in enumerate(answers):
        answer.user_token = student.student.username
        answer.save()
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=i % 2 + 2
        )
    assert student_rationale_evaluation_criterion.evaluate(student)[0] == len(
        answers
    )


def test_evaluate__part_convincing(
    student_rationale_evaluation_criterion, student, answers, teacher
):
    for i, answer in enumerate(answers[: len(answers) // 2]):
        answer.user_token = student.student.username
        answer.save()
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=i % 2 + 2
        )
    for i, answer in enumerate(
        answers[len(answers) // 2 : len(answers) * 3 // 4]
    ):
        answer.user_token = student.student.username
        answer.save()
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=1
        )
    for i, answer in enumerate(answers[len(answers) * 3 // 4 :]):
        answer.user_token = student.student.username
        answer.save()
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=0
        )
    assert (
        student_rationale_evaluation_criterion.evaluate(student)[0]
        == len(answers) // 2 - len(answers) + len(answers) * 3 // 4
    )


def test_evaluate__different_scores(
    student_rationale_evaluation_criterion, student, answers, teacher
):
    student_rationale_evaluation_criterion.points_score_3 = 2
    student_rationale_evaluation_criterion.save()
    for i, answer in enumerate(answers[: len(answers) // 4]):
        answer.user_token = student.student.username
        answer.save()
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=3
        )
    for i, answer in enumerate(answers[len(answers) // 4 : len(answers) // 2]):
        answer.user_token = student.student.username
        answer.save()
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=2
        )
    for i, answer in enumerate(
        answers[len(answers) // 2 : len(answers) * 3 // 4]
    ):
        answer.user_token = student.student.username
        answer.save()
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=1
        )
    for i, answer in enumerate(answers[len(answers) * 3 // 4 :]):
        answer.user_token = student.student.username
        answer.save()
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=0
        )
    assert (
        student_rationale_evaluation_criterion.evaluate(student)[0]
        == len(answers) // 4 * 2
        + len(answers) // 2
        - len(answers) // 4
        - len(answers)
        + len(answers) * 3 // 4
    )


def test_evaluate__wrong_model_type(
    student_rationale_evaluation_criterion, teacher
):
    with pytest.raises(TypeError):
        student_rationale_evaluation_criterion.evaluate(teacher)

    student_rationale_evaluation_criterion.for_reputation_types.add(
        ReputationType.objects.get(type="teacher")
    )
    with pytest.raises(TypeError):
        student_rationale_evaluation_criterion.evaluate(teacher)


def test_info(student_rationale_evaluation_criterion):
    info = student_rationale_evaluation_criterion.info()
    assert len(info) == 3
    assert "name" in info
    assert "full_name" in info
    assert "description" in info
