from unittest.mock import MagicMock

import pytest

from peerinst.models import ShownRationale
from peerinst.tests.fixtures import *  # noqa
from quality.models.criterion import (
    SelectedAnswerCriterion,
    SelectedAnswerCriterionRules,
)
from quality.tests.fixtures import *  # noqa


def test_info():
    info = SelectedAnswerCriterion.info()
    assert "name" in info
    assert "full_name" in info
    assert "description" in info


def test_create_default():
    n = SelectedAnswerCriterion.objects.count()
    criterion = SelectedAnswerCriterion.create_default()
    assert isinstance(criterion, SelectedAnswerCriterion)
    assert SelectedAnswerCriterion.objects.count() == n + 1


def test_evaluate__never_shown(
    selected_answer_criterion, selected_answer_rules, answers
):
    answer = answers[0]
    ShownRationale.objects.all().delete()

    selected_answer_rules.default_if_never_shown = 1
    selected_answer_rules.save()

    assert (
        selected_answer_criterion.evaluate(answer, selected_answer_rules.pk)[
            "quality"
        ]
        == 1
    )


def test_evaluate__always_selected(
    selected_answer_criterion, selected_answer_rules, answers
):
    answer = answers[0]
    for a in answers[1:]:
        a.chosen_rationale = answer
        a.save()
        ShownRationale.objects.create(shown_for_answer=a, shown_answer=answer)

    selected_answer_rules.default_if_never_shown = 0
    selected_answer_rules.save()

    assert (
        selected_answer_criterion.evaluate(answer, selected_answer_rules.pk)[
            "quality"
        ]
        == 1
    )


def test_evaluate__never_selected(
    selected_answer_criterion, selected_answer_rules, answers
):
    answer = answers[0]
    for a in answers[1:]:
        a.chosen_rationale = answers[1]
        a.save()
        ShownRationale.objects.create(shown_for_answer=a, shown_answer=answer)

    selected_answer_rules.default_if_never_shown = 1
    selected_answer_rules.save()

    assert (
        selected_answer_criterion.evaluate(answer, selected_answer_rules.pk)[
            "quality"
        ]
        == 0
    )


def test_evaluate__some_selected(
    selected_answer_criterion, selected_answer_rules, answers
):
    answer = answers[0]
    selected = [int(i % 2 == 0) for i in range(1, len(answers))]
    for a, s in zip(answers[1:], selected):
        a.chosen_rationale = answers[s]
        a.save()
        ShownRationale.objects.create(shown_for_answer=a, shown_answer=answer)

    selected_answer_rules.default_if_never_shown = 1
    selected_answer_rules.save()

    assert selected_answer_criterion.evaluate(
        answer, selected_answer_rules.pk
    )["quality"] == sum(s == 0 for s in selected) / len(selected)


def test_evaluate__default__never_shown(selected_answer_criterion, answers):
    selected_answer_rules = SelectedAnswerCriterionRules.get_or_create()
    answer = answers[0]
    ShownRationale.objects.all().delete()

    assert (
        selected_answer_criterion.evaluate(answer, selected_answer_rules.pk)[
            "quality"
        ]
        == 0
    )


def test_evaluate__default__always_selected(
    selected_answer_criterion, answers
):
    selected_answer_rules = SelectedAnswerCriterionRules.get_or_create()
    answer = answers[0]
    for a in answers[1:]:
        a.chosen_rationale = answer
        a.save()
        ShownRationale.objects.create(shown_for_answer=a, shown_answer=answer)

    assert (
        selected_answer_criterion.evaluate(answer, selected_answer_rules.pk)[
            "quality"
        ]
        == 1
    )


def test_evaluate__default__never_selected(selected_answer_criterion, answers):
    selected_answer_rules = SelectedAnswerCriterionRules.get_or_create()
    answer = answers[0]
    for a in answers[1:]:
        a.chosen_rationale = answers[1]
        a.save()
        ShownRationale.objects.create(shown_for_answer=a, shown_answer=answer)

    assert (
        selected_answer_criterion.evaluate(answer, selected_answer_rules.pk)[
            "quality"
        ]
        == 0
    )


def test_evaluate__default__some_selected(selected_answer_criterion, answers):
    selected_answer_rules = SelectedAnswerCriterionRules.get_or_create()
    answer = answers[0]
    selected = [int(i % 2 == 0) for i in range(1, len(answers))]
    for a, s in zip(answers[1:], selected):
        a.chosen_rationale = answers[s]
        a.save()
        ShownRationale.objects.create(shown_for_answer=a, shown_answer=answer)

    assert selected_answer_criterion.evaluate(
        answer, selected_answer_rules.pk
    )["quality"] == sum(s == 0 for s in selected) / len(selected)


def test_evaluate__wrong_argument(
    selected_answer_criterion, selected_answer_rules, answers
):
    answer = answers[0]

    with pytest.raises(ValueError):
        selected_answer_criterion.evaluate(
            answer.rationale, selected_answer_rules.pk
        )


def test_batch_evaluate(
    selected_answer_criterion, selected_answer_rules, answers, mocker
):
    answers = answers[:3]
    qualities = iter(range(len(answers)))
    evaluate = MagicMock(side_effect=lambda *_: next(qualities))
    mocker.patch.object(SelectedAnswerCriterion, "evaluate", evaluate)

    qualities = selected_answer_criterion.batch_evaluate(
        answers, selected_answer_rules
    )
    assert qualities == [0, 1, 2]


def test_rules(right_answer_criterion):
    right_answer_criterion.uses_rules = ["default_if_never_shown"]
    right_answer_criterion.save()
    assert right_answer_criterion.rules == ["default_if_never_shown"]


def test_dict(right_answer_criterion):
    data = dict(right_answer_criterion)
    assert "name" in data
    assert "full_name" in data
    assert "description" in data
    assert "version" in data
    assert "versions" in data
    for version in data["versions"]:
        assert "version" in version
        assert "is_beta" in version
        assert "binary_threshold" in version
        assert len(version) == 3
    assert len(data) == 5
