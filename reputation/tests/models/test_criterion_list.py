# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from reputation.models import Criterion
from reputation.models.criteria.errors import CriterionDoesNotExistError
from reputation.models.criterion_list import criteria, get_criterion


def test_get_criterion():
    for criterion in criteria:
        criterion_ = get_criterion(criterion)
        assert issubclass(criterion_, Criterion)
        assert hasattr(criterion_, "name")
        assert hasattr(criterion_, "evaluate")


def test_get_criterion__wrong():
    with pytest.raises(CriterionDoesNotExistError):
        criterion = get_criterion("fake_critertion")
