import time

from django.db.utils import IntegrityError

from peerinst.tests.fixtures import *  # noqa
from quality.models import LikelihoodCache, LikelihoodLanguage


def test_get(answers):
    answer = answers[0]
    answer.rationale = (
        "All happy families are alike; each unhappy family is unhappy in its "
        "own way."
    )
    answer.save()

    english = LikelihoodLanguage.objects.get(language="english")

    start = time.time()
    likelihood_1, likelihood_random_1 = LikelihoodCache.get(answer, english, 3)
    time_taken_1 = time.time() - start

    start = time.time()
    likelihood_2, likelihood_random_2 = LikelihoodCache.get(answer, english, 3)
    time_taken_2 = time.time() - start

    assert abs(likelihood_1 - likelihood_2) < 1e-5
    assert abs(likelihood_random_1 - likelihood_random_2) < 1e-5
    assert time_taken_2 < time_taken_1


def test_get__rationale_only(answers):
    answer = answers[0]
    answer.rationale = (
        "All happy families are alike; each unhappy family is unhappy in its "
        "own way."
    )
    answer.save()

    english = LikelihoodLanguage.objects.get(language="english")

    start = time.time()
    likelihood_1, likelihood_random_1 = LikelihoodCache.get(
        answer.rationale, english, 3
    )
    time_taken_1 = time.time() - start

    start = time.time()
    likelihood_2, likelihood_random_2 = LikelihoodCache.get(
        answer.rationale, english, 3
    )
    time_taken_2 = time.time() - start

    assert abs(likelihood_1 - likelihood_2) < 1e-5
    assert abs(likelihood_random_1 - likelihood_random_2) < 1e-5
    assert time_taken_2 < time_taken_1


def test_get__added_by_other_server(answers, mocker):
    answer = answers[0]
    answer.rationale = (
        "All happy families are alike; each unhappy family is unhappy in its "
        "own way."
    )
    answer.save()

    english = LikelihoodLanguage.objects.get(language="english")

    likelihood_1, likelihood_random_1 = LikelihoodCache.get(answer, english, 3)

    mocker.patch(
        "quality.models.criterion.criterions.likelihood.LikelihoodCache"
        ".objects.create",
        side_effect=IntegrityError(),
    )

    likelihood_2, likelihood_random_2 = LikelihoodCache.get(answer, english, 3)

    assert likelihood_1 == likelihood_2
    assert likelihood_random_1 == likelihood_random_2


def test_batch(answers):
    answers = answers[:3]
    answers[0].rationale = (
        "It is a truth universally acknowledged, that a single man in "
        "possession of a good fortune, must be in want of a wife."
    )
    answers[1].rationale = (
        "All happy families are alike; each unhappy family is unhappy in its "
        "own way."
    )
    answers[2].rationales = (
        "It was a bright cold day in April, and the clocks were striking "
        "thirteen."
    )
    for answer in answers:
        answer.save()

    english = LikelihoodLanguage.objects.get(language="english")

    start = time.time()
    likelihoods_1 = LikelihoodCache.batch(answers, english, 3)
    time_taken_1 = time.time() - start

    start = time.time()
    likelihoods_2 = LikelihoodCache.batch(answers, english, 3)
    time_taken_2 = time.time() - start

    for l1, l2 in zip(likelihoods_1, likelihoods_2):
        assert abs(l1[0] - l2[0]) < 1e-5
        assert abs(l1[1] - l2[1]) < 1e-5
    assert time_taken_2 < time_taken_1


def test_batch__rationale_only(answers):
    answers = answers[:3]
    answers[0].rationale = (
        "It is a truth universally acknowledged, that a single man in "
        "possession of a good fortune, must be in want of a wife."
    )
    answers[1].rationale = (
        "All happy families are alike; each unhappy family is unhappy in its "
        "own way."
    )
    answers[2].rationales = (
        "It was a bright cold day in April, and the clocks were striking "
        "thirteen."
    )
    for answer in answers:
        answer.save()

    english = LikelihoodLanguage.objects.get(language="english")

    start = time.time()
    likelihoods_1 = LikelihoodCache.batch(
        [a.rationale for a in answers], english, 3
    )
    time_taken_1 = time.time() - start

    start = time.time()
    likelihoods_2 = LikelihoodCache.batch(
        [a.rationale for a in answers], english, 3
    )
    time_taken_2 = time.time() - start

    for l1, l2 in zip(likelihoods_1, likelihoods_2):
        assert abs(l1[0] - l2[0]) < 1e-5
        assert abs(l1[1] - l2[1]) < 1e-5
    assert time_taken_2 < time_taken_1
