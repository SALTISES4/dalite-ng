# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from reputation.models import QuestionLikedCriterion, ReputationType


@pytest.fixture
def question_liked_criterion():
    criterion = QuestionLikedCriterion.objects.create(
        points_per_threshold=["1"]
    )
    criterion.for_reputation_types.add(
        ReputationType.objects.get(type="question"),
        ReputationType.objects.get(type="teacher"),
    )
    return criterion
