from unittest import mock

from quality.models import UsesCriterion
from quality.tests.fixtures import *  # noqa


def test_dict(assignment_validation_quality):
    with mock.patch(
        "quality.models.quality.get_criterion"
    ) as get_criterion, mock.patch("quality.models.quality.models.Model.save"):
        rules = mock.MagicMock()
        del rules.keys
        rules.__iter__.return_value = list({"a": 1, "b": 2, "c": 3}.items())

        criterion_ = mock.MagicMock()
        del criterion_.keys
        criterion_.__iter__.return_value = list(
            {
                "version": 0,
                "versions": 1,
                "is_beta": False,
                "name": "a",
                "full_name": "a",
                "description": "a",
            }.items()
        )
        criterion_.rules = ["a", "b", "c"]

        criterion_class = mock.Mock()
        criterion_class.objects.get.return_value = criterion_
        criterion_class.objects.count.return_value = 1

        criterion_rules_class = mock.Mock()
        criterion_rules_class.objects.get.return_value = rules

        get_criterion.return_value = {
            "criterion": criterion_class,
            "rules": criterion_rules_class,
        }

        criterion = UsesCriterion.objects.create(
            quality=assignment_validation_quality,
            name="fake",
            version=0,
            rules=0,
            weight=1,
        )
        data = dict(criterion)
        assert data["a"] == 1
        assert data["b"] == 2
        assert data["c"] == 3
        assert data["weight"] == 1
        assert "version" in data
        assert "versions" in data
        assert "is_beta" in data
        assert "name" in data
        assert "full_name" in data
        assert "description" in data
        assert len(data) == 10


def test_dict__subset_of_rules(assignment_validation_quality):
    with mock.patch(
        "quality.models.quality.get_criterion"
    ) as get_criterion, mock.patch("quality.models.quality.models.Model.save"):
        rules = mock.MagicMock()
        del rules.keys
        rules.__iter__.return_value = list({"a": 1, "b": 2, "c": 3}.items())

        criterion_ = mock.MagicMock()
        del criterion_.keys
        criterion_.__iter__.return_value = list(
            {
                "version": 0,
                "versions": 1,
                "is_beta": False,
                "name": "a",
                "full_name": "a",
                "description": "a",
            }.items()
        )
        criterion_.rules = ["a", "c"]

        criterion_class = mock.Mock()
        criterion_class.objects.get.return_value = criterion_
        criterion_class.objects.count.return_value = 1

        criterion_rules_class = mock.Mock()
        criterion_rules_class.objects.get.return_value = rules

        get_criterion.return_value = {
            "criterion": criterion_class,
            "rules": criterion_rules_class,
        }

        criterion = UsesCriterion.objects.create(
            quality=assignment_validation_quality,
            name="fake",
            version=0,
            rules=0,
            weight=1,
        )
        data = dict(criterion)
        assert data["a"] == 1
        assert "b" not in data
        assert data["c"] == 3
        assert data["weight"] == 1
        assert "version" in data
        assert "versions" in data
        assert "is_beta" in data
        assert "name" in data
        assert "full_name" in data
        assert "description" in data
        assert len(data) == 9


def test_str(global_validation_quality):
    criterion = UsesCriterion.objects.create(
        quality=global_validation_quality,
        name="fake",
        version=0,
        rules=0,
        weight=1,
    )
    assert str(
        criterion
    ) == "fake for quality {} for global and use type validation".format(
        global_validation_quality.pk
    )
