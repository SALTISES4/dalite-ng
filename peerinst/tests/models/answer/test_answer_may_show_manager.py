# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from peerinst.models import Answer, AnswerAnnotation
from peerinst.tests.fixtures import *  # noqa


def test_answers_with_no_annotations(answers):
    assert Answer.may_show.count() == len(answers)


def test_answers_with_all_correct_annotations(answers, teacher):
    for answer in answers:
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=3
        )

    assert Answer.may_show.count() == len(answers)


def test_answers_with_all_bad_annotations(answers, teacher):
    for answer in answers:
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=0
        )

    assert Answer.may_show.count() == 0


def test_answers_with_some_bad_and_correct_annotations(answers, teacher):
    for answer in answers[: len(answers) // 3]:
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=3
        )
    for answer in answers[len(answers) // 3 : len(answers) // 3 * 2]:
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=0
        )

    assert Answer.may_show.count() == len(answers) - len(answers) // 3
