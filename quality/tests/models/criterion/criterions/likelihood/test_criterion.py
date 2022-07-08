import random
import string

import pytest

from peerinst.tests.fixtures import *  # noqa
from quality.models.criterion import (
    LikelihoodCriterion,
    LikelihoodCriterionRules,
)
from quality.tests.fixtures import *  # noqa


def test_info():
    info = LikelihoodCriterion.info()
    assert "name" in info
    assert "full_name" in info
    assert "description" in info


def test_create_default():
    n = LikelihoodCriterion.objects.count()
    criterion = LikelihoodCriterion.create_default()
    assert isinstance(criterion, LikelihoodCriterion)
    assert LikelihoodCriterion.objects.count() == n + 1


def test_evaluate__english_french__english(
    likelihood_criterion, likelihood_rules, answers
):
    answer = answers[0]
    answer.rationale = (
        "All happy families are alike; each unhappy family is unhappy in its "
        "own way."
    )
    answer.save()

    likelihood_rules.languages.set(["english", "french"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    assert (
        likelihood_criterion.evaluate(answer, likelihood_rules.pk)["quality"]
        >= 0.95
    )


def test_evaluate__english_french__french(
    likelihood_criterion, likelihood_rules, answers
):
    answer = answers[0]
    answer.rationale = (
        "Les familles heureuses se ressemblent toutes; les familles "
        "malheureuses sont malheureuses chacune à leur façon."
    )
    answer.save()

    likelihood_rules.languages.set(["english", "french"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    assert (
        likelihood_criterion.evaluate(answer, likelihood_rules.pk)["quality"]
        >= 0.95
    )


def test_evaluate__english_french__random(
    likelihood_criterion, likelihood_rules, answers
):
    answer = answers[0]
    answer.rationale = "".join(
        random.choice([" "] + list(string.ascii_letters))
        for _ in range(random.randint(5, 50))
    )
    answer.save()

    likelihood_rules.languages.set(["english", "french"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    assert (
        likelihood_criterion.evaluate(answer, likelihood_rules.pk)["quality"]
        < 0.95
    )


def test_evaluate__english__english(
    likelihood_criterion, likelihood_rules, answers
):
    answer = answers[0]
    answer.rationale = (
        "All happy families are alike; each unhappy family is unhappy in its "
        "own way."
    )
    answer.save()

    likelihood_rules.languages.set(["english"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    assert (
        likelihood_criterion.evaluate(answer, likelihood_rules.pk)["quality"]
        >= 0.95
    )


def test_evaluate__english__french(
    likelihood_criterion, likelihood_rules, answers
):
    answer = answers[0]
    answer.rationale = (
        "Les familles heureuses se ressemblent toutes; les familles "
        "malheureuses sont malheureuses chacune à leur façon."
    )
    answer.save()

    likelihood_rules.languages.set(["english"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    assert (
        likelihood_criterion.evaluate(answer, likelihood_rules.pk)["quality"]
        < 0.95
    )


def test_evaluate__english__random(
    likelihood_criterion, likelihood_rules, answers
):
    answer = answers[0]
    answer.rationale = "".join(
        random.choice([" "] + list(string.ascii_letters))
        for _ in range(random.randint(5, 50))
    )
    answer.save()

    likelihood_rules.languages.set(["english"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    assert (
        likelihood_criterion.evaluate(answer, likelihood_rules.pk)["quality"]
        < 0.95
    )


def test_evaluate__french__english(
    likelihood_criterion, likelihood_rules, answers
):
    answer = answers[0]
    answer.rationale = (
        "All happy families are alike; each unhappy family is unhappy in its "
        "own way."
    )
    answer.save()

    likelihood_rules.languages.set(["french"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    assert (
        likelihood_criterion.evaluate(answer, likelihood_rules.pk)["quality"]
        < 0.95
    )


def test_evaluate__french__french(
    likelihood_criterion, likelihood_rules, answers
):
    answer = answers[0]
    answer.rationale = (
        "Les familles heureuses se ressemblent toutes; les familles "
        "malheureuses sont malheureuses chacune à leur façon."
    )
    answer.save()

    likelihood_rules.languages.set(["french"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    assert (
        likelihood_criterion.evaluate(answer, likelihood_rules.pk)["quality"]
        >= 0.95
    )


def test_evaluate__french__random(
    likelihood_criterion, likelihood_rules, answers
):
    answer = answers[0]
    answer.rationale = "".join(
        random.choice([" "] + list(string.ascii_letters))
        for _ in range(random.randint(5, 50))
    )
    answer.save()

    likelihood_rules.languages.set(["french"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    assert (
        likelihood_criterion.evaluate(answer, likelihood_rules.pk)["quality"]
        < 0.95
    )


def test_evaluate__default__english(likelihood_criterion, answers):
    answer = answers[0]
    answer.rationale = (
        "All happy families are alike; each unhappy family is unhappy in its "
        "own way."
    )
    answer.save()

    likelihood_rules = LikelihoodCriterionRules.get_or_create()

    assert (
        likelihood_criterion.evaluate(answer, likelihood_rules.pk)["quality"]
        >= 0.95
    )


def test_evaluate__default__french(likelihood_criterion, answers):
    answer = answers[0]
    answer.rationale = (
        "Les familles heureuses se ressemblent toutes; les familles "
        "malheureuses sont malheureuses chacune à leur façon."
    )
    answer.save()

    likelihood_rules = LikelihoodCriterionRules.get_or_create()

    assert (
        likelihood_criterion.evaluate(answer, likelihood_rules.pk)["quality"]
        >= 0.95
    )


def test_evaluate__default__random(likelihood_criterion, answers):
    answer = answers[0]
    answer.rationale = "".join(
        random.choice([" "] + list(string.ascii_letters))
        for _ in range(random.randint(5, 50))
    )
    answer.save()

    likelihood_rules = LikelihoodCriterionRules.get_or_create()

    assert (
        likelihood_criterion.evaluate(answer, likelihood_rules.pk)["quality"]
        < 0.95
    )


@pytest.mark.django_db(transaction=True)
def test_batch_evaluate__english_french__english(
    likelihood_criterion, likelihood_rules, answers
):
    answers = answers[:3]
    for answer in answers:
        answer.rationale = (
            "All happy families are alike; each unhappy family is unhappy in "
            "its own way."
        )
        answer.save()

    likelihood_rules.languages.set(["english", "french"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    quality = likelihood_criterion.batch_evaluate(answers, likelihood_rules.pk)
    for q in quality:
        assert q["quality"] >= 0.95


@pytest.mark.django_db(transaction=True)
def test_batch_evaluate__english_french__french(
    likelihood_criterion, likelihood_rules, answers
):
    answers = answers[:3]
    for answer in answers:
        answer.rationale = (
            "Les familles heureuses se ressemblent toutes; les familles "
            "malheureuses sont malheureuses chacune à leur façon."
        )
        answer.save()

    likelihood_rules.languages.set(["english", "french"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    quality = likelihood_criterion.batch_evaluate(answers, likelihood_rules.pk)
    for q in quality:
        assert q["quality"] >= 0.95


@pytest.mark.django_db(transaction=True)
def test_batch_evaluate__english_french__random(
    likelihood_criterion, likelihood_rules, answers
):
    answers = answers[:3]
    for answer in answers:
        answer.rationale = "".join(
            random.choice([" "] + list(string.ascii_letters))
            for _ in range(random.randint(5, 50))
        )
        answer.save()

    likelihood_rules.languages.set(["english", "french"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    quality = likelihood_criterion.batch_evaluate(answers, likelihood_rules.pk)
    for q in quality:
        assert q["quality"] < 0.95


@pytest.mark.django_db(transaction=True)
def test_batch_evaluate__english__english(
    likelihood_criterion, likelihood_rules, answers
):
    answers = answers[:3]
    for answer in answers:
        answer.rationale = (
            "All happy families are alike; each unhappy family is unhappy in "
            "its own way."
        )
        answer.save()

    likelihood_rules.languages.set(["english"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    quality = likelihood_criterion.batch_evaluate(answers, likelihood_rules.pk)
    for q in quality:
        assert q["quality"] >= 0.95


@pytest.mark.django_db(transaction=True)
def test_batch_evaluate__english__french(
    likelihood_criterion, likelihood_rules, answers
):
    answers = answers[:3]
    for answer in answers:
        answer.rationale = (
            "Les familles heureuses se ressemblent toutes; les familles "
            "malheureuses sont malheureuses chacune à leur façon."
        )
        answer.save()

    likelihood_rules.languages.set(["english"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    quality = likelihood_criterion.batch_evaluate(answers, likelihood_rules.pk)
    for q in quality:
        assert q["quality"] < 0.95


@pytest.mark.django_db(transaction=True)
def test_batch_evaluate__english__random(
    likelihood_criterion, likelihood_rules, answers
):
    answers = answers[:3]
    for answer in answers:
        answer.rationale = "".join(
            random.choice([" "] + list(string.ascii_letters))
            for _ in range(random.randint(5, 50))
        )
        answer.save()

    likelihood_rules.languages.set(["english"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    quality = likelihood_criterion.batch_evaluate(answers, likelihood_rules.pk)
    for q in quality:
        assert q["quality"] < 0.95


@pytest.mark.django_db(transaction=True)
def test_batch_evaluate__french__english(
    likelihood_criterion, likelihood_rules, answers
):
    answers = answers[:3]
    for answer in answers:
        answer.rationale = (
            "All happy families are alike; each unhappy family is unhappy in "
            "its own way."
        )
        answer.save()

    likelihood_rules.languages.set(["french"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    quality = likelihood_criterion.batch_evaluate(answers, likelihood_rules.pk)
    for q in quality:
        assert q["quality"] < 0.95


@pytest.mark.django_db(transaction=True)
def test_batch_evaluate__french__french(
    likelihood_criterion, likelihood_rules, answers
):
    answers = answers[:3]
    for answer in answers:
        answer.rationale = (
            "Les familles heureuses se ressemblent toutes; les familles "
            "malheureuses sont malheureuses chacune à leur façon."
        )
        answer.save()

    likelihood_rules.languages.set(["french"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    quality = likelihood_criterion.batch_evaluate(answers, likelihood_rules.pk)
    for q in quality:
        assert q["quality"] >= 0.95


@pytest.mark.django_db(transaction=True)
def test_batch_evaluate__french__random(
    likelihood_criterion, likelihood_rules, answers
):
    answers = answers[:3]
    for answer in answers:
        answer.rationale = "".join(
            random.choice([" "] + list(string.ascii_letters))
            for _ in range(random.randint(5, 50))
        )
        answer.save()

    likelihood_rules.languages.set(["french"])
    likelihood_rules.max_gram = 3
    likelihood_rules.save()

    quality = likelihood_criterion.batch_evaluate(answers, likelihood_rules.pk)
    for q in quality:
        assert q["quality"] < 0.95


@pytest.mark.django_db(transaction=True)
def test_batch_evaluate__default__english(likelihood_criterion, answers):
    answers = answers[:3]
    for answer in answers:
        answer.rationale = (
            "All happy families are alike; each unhappy family is unhappy in "
            "its own way."
        )
        answer.save()

    likelihood_rules = LikelihoodCriterionRules.get_or_create()

    quality = likelihood_criterion.batch_evaluate(answers, likelihood_rules.pk)
    for q in quality:
        assert q["quality"] >= 0.95


@pytest.mark.django_db(transaction=True)
def test_batch_evaluate__default__french(likelihood_criterion, answers):
    answers = answers[:3]
    for answer in answers:
        answer.rationale = (
            "Les familles heureuses se ressemblent toutes; les familles "
            "malheureuses sont malheureuses chacune à leur façon."
        )
        answer.save()

    likelihood_rules = LikelihoodCriterionRules.get_or_create()

    quality = likelihood_criterion.batch_evaluate(answers, likelihood_rules.pk)
    for q in quality:
        assert q["quality"] >= 0.95


@pytest.mark.django_db(transaction=True)
def test_batch_evaluate__default__random(likelihood_criterion, answers):
    answers = answers[:3]
    for answer in answers:
        answer.rationale = "".join(
            random.choice([" "] + list(string.ascii_letters))
            for _ in range(random.randint(5, 50))
        )
        answer.save()

    likelihood_rules = LikelihoodCriterionRules.get_or_create()

    quality = likelihood_criterion.batch_evaluate(answers, likelihood_rules.pk)
    for q in quality:
        assert q["quality"] < 0.95


def test_rules(likelihood_criterion):
    likelihood_criterion.uses_rules = ["a", "b", "c", "d"]
    likelihood_criterion.save()
    assert likelihood_criterion.rules == ["a", "b", "c", "d"]


def test_dict(likelihood_criterion):
    data = dict(likelihood_criterion)
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
