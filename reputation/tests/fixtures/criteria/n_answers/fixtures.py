import pytest

from reputation.models import NAnswersCriterion, ReputationType


@pytest.fixture
def n_answers_criterion():
    criterion = NAnswersCriterion.objects.create(points_per_threshold=["1"])
    criterion.for_reputation_types.add(
        ReputationType.objects.get(type="question"),
        ReputationType.objects.get(type="student"),
    )
    return criterion
