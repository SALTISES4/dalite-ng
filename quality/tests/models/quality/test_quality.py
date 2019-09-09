# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import time

import mock
import pytest

from quality.models import (
    MinWordsCriterionRules,
    NegWordsCriterionRules,
    QualityCache,
    UsesCriterion,
)
from quality.tests.fixtures import *  # noqa


def test_str(global_validation_quality, assignment_validation_quality):
    assert (
        str(global_validation_quality)
        == "{} for global ".format(global_validation_quality.pk)
        + "and use type validation"
    )
    assert (
        str(assignment_validation_quality)
        == "{} for studentgroupassignment: None ".format(
            assignment_validation_quality.pk
        )
        + "and use type validation"
    )


def test_dict(assignment_validation_quality):
    data = dict(assignment_validation_quality)
    assert len(data) == 3
    assert "pk" in data
    assert "quality_type" in data
    assert "quality_use_type" in data


def test_evaluate__no_criterions(assignment_validation_quality):
    answer = mock.Mock()

    quality_, qualities = assignment_validation_quality.evaluate(answer)

    assert quality_ is None
    assert qualities == []


def test_evaluate__all_equal(assignment_validation_quality):
    answer = mock.Mock()

    for i in range(3):
        UsesCriterion.objects.create(
            quality=assignment_validation_quality,
            name="fake_{}".format(i + 1),
            version=0,
            rules=0,
            weight=1,
        )

    with mock.patch("quality.models.quality.get_criterion") as get_criterion:

        criterion_class = mock.Mock()
        get_criterion.return_value = {
            "criterion": criterion_class,
            "rules": mock.Mock(),
        }

        criterion = mock.MagicMock()
        criterion.__iter__.side_effect = {}.__iter__
        evaluations = ({"quality": i + 1, "threshold": 1} for i in range(3))
        criterion.evaluate = lambda answer, rules: next(evaluations)

        criterion_class.objects.get.return_value = criterion

        quality_, qualities = assignment_validation_quality.evaluate(answer)

        assert quality_ == (1.0 + 2 + 3) / 3
        for i, q in enumerate(qualities):
            assert q["quality"]["quality"] == i + 1
            assert q["weight"] == 1


def test_evaluate__different_weights(assignment_validation_quality):
    answer = mock.Mock()

    for i in range(3):
        UsesCriterion.objects.create(
            quality=assignment_validation_quality,
            name="fake_{}".format(i + 1),
            version=0,
            rules=0,
            weight=i + 1,
        )

    with mock.patch("quality.models.quality.get_criterion") as get_criterion:

        criterion_class = mock.Mock()
        get_criterion.return_value = {
            "criterion": criterion_class,
            "rules": mock.Mock(),
        }

        criterion = mock.MagicMock()
        criterion.__iter__.side_effect = {}.__iter__
        evaluations = ({"quality": i + 1, "threshold": 1} for i in range(3))
        criterion.evaluate = lambda answer, rules: next(evaluations)

        criterion_class.objects.get.return_value = criterion

        quality_, qualities = assignment_validation_quality.evaluate(answer)

        assert quality_ == ((1.0 * 1 + 2 * 2 + 3 * 3) / (1 + 2 + 3))
        for i, q in enumerate(qualities):
            assert q["quality"]["quality"] == i + 1
            assert q["weight"] == i + 1


def test_evaluate__cached(assignment_validation_quality):
    answer = mock.Mock()
    answer.pk = 0
    answer.rationale = "test"

    for i in range(3):
        UsesCriterion.objects.create(
            quality=assignment_validation_quality,
            name="fake_{}".format(i + 1),
            version=0,
            rules=0,
            weight=1,
        )

    with mock.patch("quality.models.quality.get_criterion") as get_criterion:

        criterion_class = mock.Mock()
        get_criterion.return_value = {
            "criterion": criterion_class,
            "rules": mock.Mock(),
        }

        criterion = mock.MagicMock()
        criterion.__iter__.side_effect = {}.__iter__

        def evaluate():
            i = 0
            while True:
                time.sleep(0.1)
                i += 1
                yield {"quality": i + 1, "threshold": 1}

        evaluations = evaluate()
        criterion.evaluate = lambda answer, rules: next(evaluations)

        criterion_class.objects.get.return_value = criterion

        start = time.time()
        quality_1, qualities_1 = assignment_validation_quality.evaluate(
            answer, cache=True
        )
        time_taken_1 = time.time() - start

        start = time.time()
        quality_2, qualities_2 = assignment_validation_quality.evaluate(
            answer, cache=True
        )
        time_taken_2 = time.time() - start

        assert time_taken_2 < time_taken_1
        assert quality_1 == quality_2
        assert qualities_1 == qualities_2


def test_batch_evaluate__no_criterions(assignment_validation_quality):
    answers = [mock.Mock() for _ in range(3)]

    qualities = assignment_validation_quality.batch_evaluate(answers)
    for (quality, _qualities) in qualities:
        assert quality is None
        assert _qualities == []


def test_batch_evaluate__all_equal(assignment_validation_quality):
    answers = [mock.Mock() for _ in range(3)]

    for i in range(3):
        UsesCriterion.objects.create(
            quality=assignment_validation_quality,
            name="fake_{}".format(i + 1),
            version=0,
            rules=0,
            weight=1,
        )

    with mock.patch("quality.models.quality.get_criterion") as get_criterion:

        criterion_class = mock.Mock()
        get_criterion.return_value = {
            "criterion": criterion_class,
            "rules": mock.Mock(),
        }

        criterion = mock.MagicMock()
        criterion.__iter__.side_effect = {}.__iter__
        evaluations = (
            [{"quality": i + 1, "threshold": 1} for _ in range(len(answers))]
            for i in range(3)
        )
        criterion.batch_evaluate = lambda answer, rules: next(evaluations)

        criterion_class.objects.get.return_value = criterion

        qualities = assignment_validation_quality.batch_evaluate(answers)

        for (quality, _qualities) in qualities:
            assert quality == (1.0 + 2 + 3) / 3
            for i, q in enumerate(_qualities):
                assert q["quality"]["quality"] == i + 1
                assert q["weight"] == 1


def test_batch_evaluate__different_weights(assignment_validation_quality):
    answers = [mock.Mock() for _ in range(3)]

    for i in range(3):
        UsesCriterion.objects.create(
            quality=assignment_validation_quality,
            name="fake_{}".format(i + 1),
            version=0,
            rules=0,
            weight=i + 1,
        )

    with mock.patch("quality.models.quality.get_criterion") as get_criterion:

        criterion_class = mock.Mock()
        get_criterion.return_value = {
            "criterion": criterion_class,
            "rules": mock.Mock(),
        }

        criterion = mock.MagicMock()
        criterion.__iter__.side_effect = {}.__iter__
        evaluations = (
            [{"quality": i + 1, "threshold": 1} for _ in range(len(answers))]
            for i in range(3)
        )
        criterion.batch_evaluate = lambda answer, rules: next(evaluations)

        criterion_class.objects.get.return_value = criterion

        qualities = assignment_validation_quality.batch_evaluate(answers)

        for (quality, _qualities) in qualities:
            assert quality == ((1.0 * 1 + 2 * 2 + 3 * 3) / (1 + 2 + 3))
            for i, q in enumerate(_qualities):
                assert q["quality"]["quality"] == i + 1
                assert q["weight"] == i + 1


def test_batch_evaluate__cached_all(assignment_validation_quality):
    answers = [mock.Mock() for _ in range(3)]
    for i, answer in enumerate(answers):
        answer.pk = i
        answer.rationale = "test" + str(i)

    for i in range(3):
        UsesCriterion.objects.create(
            quality=assignment_validation_quality,
            name="fake_{}".format(i + 1),
            version=0,
            rules=0,
            weight=1,
        )

    with mock.patch("quality.models.quality.get_criterion") as get_criterion:

        criterion_class = mock.Mock()
        get_criterion.return_value = {
            "criterion": criterion_class,
            "rules": mock.Mock(),
        }

        criterion = mock.MagicMock()
        criterion.__iter__.side_effect = {}.__iter__

        def evaluate():
            i = 0
            while True:
                time.sleep(0.1)
                i += 1
                yield [
                    {"quality": i + 1, "threshold": 1}
                    for _ in range(len(answers))
                ]

        evaluations = evaluate()
        criterion.batch_evaluate = lambda answer, rules: next(evaluations)

        criterion_class.objects.get.return_value = criterion

        start = time.time()
        qualities_1 = assignment_validation_quality.batch_evaluate(
            answers, cache=True
        )
        time_taken_1 = time.time() - start

        evaluations = evaluate()
        criterion.batch_evaluate = lambda answer, rules: next(evaluations)

        start = time.time()
        qualities_2 = assignment_validation_quality.batch_evaluate(
            answers, cache=True
        )
        time_taken_2 = time.time() - start

        assert time_taken_2 < time_taken_1
        assert qualities_1 == qualities_2


def test_batch_evaluate__cached_some(assignment_validation_quality):
    answers = [mock.Mock() for _ in range(3)]
    for i, answer in enumerate(answers):
        answer.pk = i
        answer.rationale = "test" + str(i)

    for i in range(3):
        UsesCriterion.objects.create(
            quality=assignment_validation_quality,
            name="fake_{}".format(i + 1),
            version=0,
            rules=0,
            weight=1,
        )

    with mock.patch("quality.models.quality.get_criterion") as get_criterion:

        criterion_class = mock.Mock()
        get_criterion.return_value = {
            "criterion": criterion_class,
            "rules": mock.Mock(),
        }

        criterion = mock.MagicMock()
        criterion.__iter__.side_effect = {}.__iter__

        def evaluate():
            i = 0
            while True:
                time.sleep(0.1)
                i += 1
                yield [
                    {"quality": i + 1, "threshold": 1}
                    for _ in range(len(answers))
                ]

        evaluations = evaluate()
        criterion.batch_evaluate = lambda answer, rules: next(evaluations)

        criterion_class.objects.get.return_value = criterion

        start = time.time()
        qualities_1 = assignment_validation_quality.batch_evaluate(
            answers, cache=True
        )
        time_taken_1 = time.time() - start

        for c in QualityCache.objects.all()[:2]:
            c.delete()

        evaluations = evaluate()
        criterion.batch_evaluate = lambda answer, rules: next(evaluations)

        evaluations = evaluate()
        criterion.batch_evaluate = lambda answer, rules: next(evaluations)

        start = time.time()
        qualities_2 = assignment_validation_quality.batch_evaluate(
            answers, cache=True
        )
        time_taken_2 = time.time() - start

        assert time_taken_2 < time_taken_1
        assert qualities_1 == qualities_2


def test_add_criterion(assignment_validation_quality):

    with mock.patch(
        "quality.models.quality.get_criterion"
    ) as get_criterion, mock.patch(
        "quality.models.quality.UsesCriterion.save"
    ) as uses_criterion_save, mock.patch(
        "quality.models.quality.criterions"
    ) as criterions:

        criterion_class = mock.Mock()
        criterion_class.objects.filter.exists.return_value = True
        criterion_class.info.return_value = {"name": "test"}
        criterions_ = [{"criterion": criterion_class, "rules": mock.Mock()}]
        criterions.values.return_value = criterions_

        criterion = mock.Mock()
        criterion.pk = 0
        criterion_ = mock.Mock()
        criterion_.objects.get.return_value = criterion
        rules = mock.Mock()
        rules.pk = 0

        get_criterion.return_value = {"criterion": criterion, "rules": rules}

        assignment_validation_quality.add_criterion("test")

        assert uses_criterion_save.called


def test_add_criterion__invalid_name(assignment_validation_quality):
    with mock.patch("quality.models.quality.criterions") as criterions:

        criterions.values.return_value = []

        with pytest.raises(ValueError):
            assignment_validation_quality.add_criterion("test")


def test_update_criterion__general_rule(assignment_validation_quality):
    UsesCriterion.objects.create(
        quality=assignment_validation_quality,
        name="test",
        version=0,
        rules=0,
        weight=1,
    )

    (
        criterion,
        old_value,
        value,
    ) = assignment_validation_quality.update_criterion("test", "version", 1)
    assert criterion.version == 1
    assert (
        UsesCriterion.objects.get(
            quality=assignment_validation_quality, name="test"
        ).version
        == 1
    )
    assert old_value == 0
    assert value == 1

    (
        criterion,
        old_value,
        value,
    ) = assignment_validation_quality.update_criterion("test", "weight", 2)
    assert criterion.weight == 2
    assert (
        UsesCriterion.objects.get(
            quality=assignment_validation_quality, name="test"
        ).weight
        == 2
    )
    assert old_value == 1
    assert value == 2


def test_update_criterion__specific_rule(
    assignment_validation_quality, min_words_criterion, min_words_rules
):
    UsesCriterion.objects.create(
        quality=assignment_validation_quality,
        name="min_words",
        version=min_words_criterion.pk,
        rules=min_words_rules.pk,
        weight=1,
    )
    old_value_ = MinWordsCriterionRules.objects.get(
        pk=min_words_rules.pk
    ).min_words
    (
        criterion,
        old_value,
        value,
    ) = assignment_validation_quality.update_criterion(
        "min_words", "min_words", old_value_ + 1
    )

    data = dict(criterion)
    assert data["min_words"]["value"] == old_value_ + 1
    assert (
        MinWordsCriterionRules.objects.get(pk=min_words_rules.pk).min_words
        == old_value_ + 1
    )
    assert old_value == old_value_
    assert value == old_value_ + 1


def test_update_criterion__specific_rule__comma_sep_field__added(
    assignment_validation_quality, neg_words_criterion, neg_words_rules
):
    UsesCriterion.objects.create(
        quality=assignment_validation_quality,
        name="neg_words",
        version=neg_words_criterion.pk,
        rules=neg_words_rules.pk,
        weight=1,
    )
    criterion_ = NegWordsCriterionRules.objects.get(pk=neg_words_rules.pk)
    criterion_.neg_words = ["a", "b", "c"]
    criterion_.save()
    old_value_ = criterion_.neg_words
    (
        criterion,
        old_value,
        value,
    ) = assignment_validation_quality.update_criterion(
        "neg_words", "neg_words", "d"
    )

    data = dict(criterion)
    assert data["neg_words"]["value"] == ["a", "b", "c", "d"]
    assert NegWordsCriterionRules.objects.get(
        pk=neg_words_rules.pk
    ).neg_words == ["a", "b", "c", "d"]
    assert old_value == old_value_
    assert value == ["a", "b", "c", "d"]


def test_update_criterion__specific_rule__comma_sep_field__removed(
    assignment_validation_quality, neg_words_criterion, neg_words_rules
):
    UsesCriterion.objects.create(
        quality=assignment_validation_quality,
        name="neg_words",
        version=neg_words_criterion.pk,
        rules=neg_words_rules.pk,
        weight=1,
    )
    criterion_ = NegWordsCriterionRules.objects.get(pk=neg_words_rules.pk)
    criterion_.neg_words = ["a", "b", "c"]
    criterion_.save()
    old_value_ = criterion_.neg_words
    (
        criterion,
        old_value,
        value,
    ) = assignment_validation_quality.update_criterion(
        "neg_words", "neg_words", ""
    )

    data = dict(criterion)
    assert data["neg_words"]["value"] == ["a", "b"]
    assert NegWordsCriterionRules.objects.get(
        pk=neg_words_rules.pk
    ).neg_words == ["a", "b"]
    assert old_value == old_value_
    assert value == ["a", "b"]


def test_update_criterion__invalid_name(assignment_validation_quality):
    with pytest.raises(UsesCriterion.DoesNotExist):
        assignment_validation_quality.update_criterion("fake", "fake", None)


def test_update_criterion__invalid_field(
    assignment_validation_quality, min_words_criterion, min_words_rules
):
    UsesCriterion.objects.create(
        quality=assignment_validation_quality,
        name="min_words",
        version=min_words_criterion.pk,
        rules=min_words_rules.pk,
        weight=1,
    )
    with pytest.raises(KeyError):
        assignment_validation_quality.update_criterion(
            "min_words", "fake", None
        )


def test_remove_criterion(assignment_validation_quality):
    UsesCriterion.objects.create(
        quality=assignment_validation_quality,
        name="test",
        version=0,
        rules=0,
        weight=1,
    )
    UsesCriterion.objects.create(
        quality=assignment_validation_quality,
        name="test2",
        version=0,
        rules=0,
        weight=1,
    )
    assert (
        UsesCriterion.objects.filter(
            quality=assignment_validation_quality
        ).count()
        == 2
    )
    assignment_validation_quality.remove_criterion("test")
    assert (
        UsesCriterion.objects.filter(
            quality=assignment_validation_quality
        ).count()
        == 1
    )


def test_remove_criterion__doesnt_exist(assignment_validation_quality):
    UsesCriterion.objects.create(
        quality=assignment_validation_quality,
        name="test",
        version=0,
        rules=0,
        weight=1,
    )
    assert (
        UsesCriterion.objects.filter(
            quality=assignment_validation_quality
        ).count()
        == 1
    )
    assignment_validation_quality.remove_criterion("fake")
    assert (
        UsesCriterion.objects.filter(
            quality=assignment_validation_quality
        ).count()
        == 1
    )


def test_available(assignment_validation_quality):

    with mock.patch("quality.models.quality.criterions") as criterions:
        criterions_ = [
            {"criterion": mock.Mock(), "rules": mock.Mock()} for _ in range(3)
        ]
        for criterion in criterions_:
            criterion["criterion"].objects.filter.exists.return_value = True
            criterion["criterion"].info.return_value = {"name": "a"}
        criterions.values.return_value = criterions_
        available_info = assignment_validation_quality.available
        assert len(available_info) == 3
        for criterion_ in available_info:
            assert isinstance(criterion_, dict)
