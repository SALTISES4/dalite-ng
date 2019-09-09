# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest

from peerinst.models import AnswerAnnotation
from peerinst.rationale_annotation import choose_rationales
from peerinst.tests.fixtures import *  # noqa
from quality.models import Quality
from quality.tests.fixtures import *  # noqa


def test_choose_rationales(teacher, answers, discipline):
    teacher.disciplines.add(discipline)
    for answer in answers:
        answer.question.discipline = discipline
        answer.question.save()

    with mock.patch("peerinst.rationale_annotation.Quality") as Quality:
        qualities = [float(i) / len(answers) for i in range(len(answers))]
        Quality.objects.filter.return_value.exists.return_value = True
        Quality.objects.get.return_value.batch_evaluate.return_value = [
            (q, None) for q in qualities
        ]
        chosen = choose_rationales(teacher, n=5)
        assert len(chosen) == 5

        for a, a_ in zip(chosen, answers[::-1]):
            assert a == a_


def test_choose_rationales__wrong_inputs(student, teacher):
    with pytest.raises(AssertionError):
        choose_rationales(student, 3)
    with pytest.raises(AssertionError):
        choose_rationales(teacher, "3")


def test_choose_rationales__no_quality(teacher, answers, discipline):
    teacher.disciplines.add(discipline)
    for answer in answers:
        answer.question.discipline = discipline
        answer.question.save()
    Quality.objects.all().delete()
    chosen = choose_rationales(teacher, n=5)
    assert len(chosen) == 5

    for a, a_ in zip(chosen, chosen[1:]):
        assert a.datetime_first >= a_.datetime_first


def test_choose_rationales__no_answers(teacher):
    assert choose_rationales(teacher) == []


def test_choose_rationales__all_annotated(teacher, answers, discipline):
    teacher.disciplines.add(discipline)
    for answer in answers:
        answer.question.discipline = discipline
        answer.question.save()
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=0
        )
    assert choose_rationales(teacher) == []


def test_choose_rationales__some_annotated(teacher, answers, discipline):
    teacher.disciplines.add(discipline)
    for answer in answers:
        answer.question.discipline = discipline
        answer.question.save()
    for answer in answers[1::2]:
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=0
        )

    with mock.patch("peerinst.rationale_annotation.Quality") as Quality:
        qualities = [float(i) / len(answers) for i in range(len(answers))]
        Quality.objects.filter.return_value.exists.return_value = True
        Quality.objects.get.return_value.batch_evaluate.return_value = [
            (q, None) for q in qualities[::2]
        ]

        chosen = choose_rationales(teacher, n=5)
        assert len(chosen) == 5

        for a, a_ in zip(chosen, answers[::2][::-1]):
            assert a == a_


def test_choose_rationales__different_discipline(
    teacher, answers, questions, disciplines
):
    teacher.disciplines.add(disciplines[0])
    questions[0].discipline = disciplines[0]
    questions[0].save()
    questions[1].discipline = disciplines[1]
    questions[1].save()
    for answer in answers[::2]:
        answer.question = questions[0]
        answer.save()
    for answer in answers[1::2]:
        answer.question = questions[1]
        answer.save()

    with mock.patch("peerinst.rationale_annotation.Quality") as Quality:
        qualities = [float(i) / len(answers) for i in range(len(answers))]
        Quality.objects.filter.return_value.exists.return_value = True
        Quality.objects.get.return_value.batch_evaluate.return_value = [
            (q, None) for q in qualities[::2]
        ]

        chosen = choose_rationales(teacher, n=5)
        assert len(chosen) == 5

        for a, a_ in zip(chosen, answers[::2][::-1]):
            assert a == a_
