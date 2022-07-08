import pytest

from quality.models.criterion import RightAnswerCriterionRules
from quality.tests.fixtures import *  # noqa


def test_str(right_answer_rules):
    assert (
        str(right_answer_rules)
        == f"Rules {right_answer_rules.pk} for criterion right_answer"
    )


def test_get_or_create__create():
    only_last = True

    criterion = RightAnswerCriterionRules.get_or_create(only_last=only_last)
    assert criterion.only_last == only_last


def test_get_or_create__get(right_answer_rules):
    only_last = right_answer_rules.only_last
    threshold = right_answer_rules.threshold
    n_rules = RightAnswerCriterionRules.objects.count()

    criterion = RightAnswerCriterionRules.get_or_create(
        threshold=threshold, only_last=only_last
    )
    assert criterion.only_last == only_last
    assert RightAnswerCriterionRules.objects.count() == n_rules


def test_get_or_create__wrong_args():
    threshold = 2
    with pytest.raises(ValueError):
        criterion = RightAnswerCriterionRules.get_or_create(
            threshold=threshold
        )


def test_dict(right_answer_rules):
    right_answer_rules.only_last = True
    right_answer_rules.save()

    data = dict(right_answer_rules)
    assert len(data) == 2
    assert data["threshold"]["name"] == "threshold"
    assert data["threshold"]["full_name"] == "Threshold"
    assert (
        data["threshold"]["description"]
        == "Minimum value for the answer to be accepted"
    )
    assert data["threshold"]["value"] == 1
    assert data["threshold"]["type"] == "ProbabilityField"
    assert data["threshold"]["allowed"] is None
    assert len(data["threshold"]) == 6
    assert data["only_last"]["name"] == "only_last"
    assert data["only_last"]["full_name"] == "Only last step evaluated"
    assert data["only_last"]["description"] == (
        "Only the second step (or first if no second step) is evaluated. "
        "If false, both steps are evaluated."
    )
    assert data["only_last"]["value"]
    assert data["only_last"]["type"] == "BooleanField"
    assert data["only_last"]["allowed"] is None
    assert len(data["only_last"]) == 6
