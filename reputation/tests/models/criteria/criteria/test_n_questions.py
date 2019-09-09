# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from peerinst.tests.fixtures import *  # noqa
from reputation.models import ReputationType
from reputation.tests.fixtures import *  # noqa


def test_dict(n_questions_criterion):
    data = dict(n_questions_criterion)
    assert len(data) == 8
    assert "version" in data
    assert "points_per_threshold" in data
    assert "thresholds" in data
    assert "badge_thresholds" in data
    assert "badge_colour" in data
    assert "name" in data
    assert "full_name" in data
    assert "description" in data


def test_evaluate(n_questions_criterion, teacher, questions):
    assert n_questions_criterion.evaluate(teacher)[0] == len(
        [q for q in questions if q.user == teacher.user]
    )


def test_evaluate__wrong_model_type(n_questions_criterion, question):
    with pytest.raises(TypeError):
        n_questions_criterion.evaluate(question)

    n_questions_criterion.for_reputation_types.add(
        ReputationType.objects.get(type="question")
    )
    with pytest.raises(TypeError):
        n_questions_criterion.evaluate(question)


def test_info(n_questions_criterion):
    info = n_questions_criterion.info()
    assert len(info) == 3
    assert "name" in info
    assert "full_name" in info
    assert "description" in info
