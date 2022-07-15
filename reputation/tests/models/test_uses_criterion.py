from unittest import mock

from peerinst.tests.fixtures import *  # noqa
from reputation.models import UsesCriterion
from reputation.tests.fixtures import *  # noqa


def test_dict(question_reputation):
    with mock.patch(
        "reputation.models.reputation_type.get_criterion"
    ) as get_criterion, mock.patch(
        "reputation.models.reputation_type.models.Model.save"
    ):
        criterion_ = mock.MagicMock()
        del criterion_.keys
        criterion_.__iter__.return_value = list(
            {
                "version": 0,
                "name": "a",
                "full_name": "a",
                "description": "a",
            }.items()
        )

        criterion_class = mock.Mock()
        criterion_class.objects.get.return_value = criterion_
        criterion_class.objects.count.return_value = 1

        get_criterion.return_value = criterion_class

        criterion = UsesCriterion.objects.create(
            reputation_type=question_reputation.reputation_type,
            name="fake",
            version=1,
        )
        data = dict(criterion)
        assert "version" in data
        assert "name" in data
        assert "full_name" in data
        assert "description" in data
        assert len(data) == 4


def test_str(question_reputation):
    criterion = UsesCriterion.objects.create(
        reputation_type=question_reputation.reputation_type,
        name="fake",
        version=1,
    )
    assert str(criterion) == "fake for reputation type {}".format(
        question_reputation.reputation_type.type
    )
