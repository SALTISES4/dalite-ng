# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from peerinst.models import AnswerAnnotation
from peerinst.tests.fixtures import *  # noqa
from reputation.models import ReputationType
from reputation.tests.fixtures import *  # noqa


def test_dict(rationale_evaluation_criterion):
    data = dict(rationale_evaluation_criterion)
    assert len(data) == 8
    assert "version" in data
    assert "points_per_threshold" in data
    assert "thresholds" in data
    assert "badge_thresholds" in data
    assert "badge_colour" in data
    assert "name" in data
    assert "full_name" in data
    assert "description" in data


def test_evaluate__teacher(rationale_evaluation_criterion, teacher, answers):
    for i, answer in enumerate(answers):
        AnswerAnnotation.objects.create(
            answer=answer, annotator=teacher.user, score=i % 4
        )

    assert rationale_evaluation_criterion.evaluate(teacher)[0] == len(answers)


def test_evaluate__wrong_model_type(rationale_evaluation_criterion, student):
    with pytest.raises(TypeError):
        rationale_evaluation_criterion.evaluate(student)

    rationale_evaluation_criterion.for_reputation_types.add(
        ReputationType.objects.get(type="student")
    )
    with pytest.raises(TypeError):
        rationale_evaluation_criterion.evaluate(student)


def test_info(rationale_evaluation_criterion):
    info = rationale_evaluation_criterion.info()
    assert len(info) == 3
    assert "name" in info
    assert "full_name" in info
    assert "description" in info
