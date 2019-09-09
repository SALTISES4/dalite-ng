# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from reputation.models import (
    ReputationType,
    StudentRationaleEvaluationCriterion,
)


@pytest.fixture
def student_rationale_evaluation_criterion():
    criterion = StudentRationaleEvaluationCriterion.objects.create(
        points_per_threshold=["1"]
    )
    criterion.for_reputation_types.add(
        ReputationType.objects.get(type="student")
    )
    return criterion
