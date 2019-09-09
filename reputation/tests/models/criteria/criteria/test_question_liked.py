# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from peerinst.tests.fixtures import *  # noqa
from reputation.models import ReputationType
from reputation.tests.fixtures import *  # noqa


def test_dict(question_liked_criterion):
    data = dict(question_liked_criterion)
    assert len(data) == 8
    assert "version" in data
    assert "points_per_threshold" in data
    assert "thresholds" in data
    assert "badge_thresholds" in data
    assert "badge_colour" in data
    assert "name" in data
    assert "full_name" in data
    assert "description" in data


def test_evaluate__question__not_liked_used(
    question_liked_criterion, question
):
    assert question_liked_criterion.evaluate(question)[0] == 0


def test_evaluate__question__liked_used(
    question_liked_criterion, question, assignment, teacher, answers
):
    teacher.favourite_questions.add(question)
    assignment.questions.add(question)
    answers[0].assignment = assignment
    answers[0].save()
    assert question_liked_criterion.evaluate(question)[0] == 3


def test_evaluate__question__liked_not_used(
    question_liked_criterion, question, assignment, teacher
):
    teacher.favourite_questions.add(question)
    assignment.questions.add(question)
    assert question_liked_criterion.evaluate(question)[0] == 1


def test_evaluate__teacher__not_liked_used(
    question_liked_criterion, teacher, questions
):
    assert question_liked_criterion.evaluate(teacher)[0] == 0


def test_evaluate__teacher__liked_used(
    question_liked_criterion, questions, assignment, teachers, answers
):
    assignment.owner.add(teachers[1].user)
    for question in questions:
        question.user = teachers[0].user
        question.save()
        teachers[1].favourite_questions.add(question)
        assignment.questions.add(question)
    for i in range(min(len(questions), len(answers))):
        answers[i].question = questions[i]
        answers[i].assignment = assignment
        answers[i].save()

    assert question_liked_criterion.evaluate(teachers[0])[0] == 3 * min(
        len(questions), len(answers)
    )


def test_evaluate__teacher__liked_used_self(
    question_liked_criterion, questions, assignment, teachers, answers
):
    assignment.owner.add(teachers[0].user)
    for question in questions:
        question.user = teachers[0].user
        question.save()
        teachers[0].favourite_questions.add(question)
        assignment.questions.add(question)
    for i in range(min(len(questions), len(answers))):
        answers[i].question = questions[i]
        answers[i].assignment = assignment
        answers[i].save()

    assert question_liked_criterion.evaluate(teachers[0])[0] == 0


def test_evaluate__wrong_model_type(question_liked_criterion, student):
    with pytest.raises(TypeError):
        question_liked_criterion.evaluate(student)

    question_liked_criterion.for_reputation_types.add(
        ReputationType.objects.get(type="student")
    )
    with pytest.raises(TypeError):
        question_liked_criterion.evaluate(student)


def test_info(question_liked_criterion):
    info = question_liked_criterion.info()
    assert len(info) == 3
    assert "name" in info
    assert "full_name" in info
    assert "description" in info
