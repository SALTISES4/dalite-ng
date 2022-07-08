import pytest

from peerinst.tests.fixtures import *  # noqa
from reputation.models import ReputationType
from reputation.tests.fixtures import *  # noqa


def test_dict(n_answers_criterion):
    data = dict(n_answers_criterion)
    assert len(data) == 9
    assert "version" in data
    assert "points_per_threshold" in data
    assert "thresholds" in data
    assert "badge_thresholds" in data
    assert "badge_icon" in data
    assert "badge_colour" in data
    assert "name" in data
    assert "full_name" in data
    assert "description" in data


def test_evaluate__question(n_answers_criterion, question, answers):
    assert n_answers_criterion.evaluate(question)[0] == len(
        [a for a in answers if a.question == question]
    )


def test_evaluate__student(n_answers_criterion, student, answers):
    for answer in answers:
        answer.user_token = student.student.username
        answer.save()
    assert n_answers_criterion.evaluate(student)[0] == len(answers)


def test_evaluate__wrong_model_type(n_answers_criterion, teacher):
    with pytest.raises(TypeError):
        n_answers_criterion.evaluate(teacher)

    n_answers_criterion.for_reputation_types.add(
        ReputationType.objects.get(type="teacher")
    )
    with pytest.raises(TypeError):
        n_answers_criterion.evaluate(teacher)


def test_info(n_answers_criterion):
    info = n_answers_criterion.info()
    assert len(info) == 3
    assert "name" in info
    assert "full_name" in info
    assert "description" in info
