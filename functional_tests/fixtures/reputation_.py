import pytest

from reputation.models import ReputationType, UsesCriterion
from reputation.tests.fixtures import *  # noqa


@pytest.fixture
def student_reputation_with_criteria(n_answers_criterion):
    reputation = ReputationType.objects.get(type="student")
    n_answers_criterion.for_reputation_types.add(reputation)
    UsesCriterion.objects.create(
        reputation_type=reputation, name="n_answers", version=1
    )
    return reputation
