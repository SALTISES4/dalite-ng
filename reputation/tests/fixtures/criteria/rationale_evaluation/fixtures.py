import pytest

from reputation.models import RationaleEvaluationCriterion, ReputationType


@pytest.fixture
def rationale_evaluation_criterion():
    criterion = RationaleEvaluationCriterion.objects.create(
        points_per_threshold=["1"]
    )
    criterion.for_reputation_types.add(
        ReputationType.objects.get(type="teacher")
    )
    return criterion
