import pytest

from reputation.models import NQuestionsCriterion, ReputationType


@pytest.fixture
def n_questions_criterion():
    criterion = NQuestionsCriterion.objects.create(points_per_threshold=["1"])
    criterion.for_reputation_types.add(
        ReputationType.objects.get(type="teacher")
    )
    return criterion
