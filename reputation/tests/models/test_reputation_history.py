import json
from unittest import mock

import pytest

from peerinst.tests.fixtures import *  # noqa
from reputation.models import ReputationHistory
from reputation.tests.fixtures import *  # noqa


def test_create__doesnt_exist(teacher_reputation):
    reputation = (
        1,
        [
            {
                "name": "fake",
                "full_name": "fake",
                "description": "fake",
                "version": 1,
                "weight": 1,
                "reputation": 1,
            }
        ],
    )
    with mock.patch.object(
        teacher_reputation, "evaluate", return_value=reputation
    ):
        history_elem = ReputationHistory.create(teacher_reputation)
        assert history_elem.reputation.pk == teacher_reputation.pk
        assert history_elem.reputation_value == reputation[0]
        assert json.loads(history_elem.reputation_details) == reputation[1]


@pytest.mark.django_db(transaction=True)
def test_create__exists(teacher_reputation):
    reputation_1 = (
        1,
        [
            {
                "name": "fake",
                "full_name": "fake",
                "description": "fake",
                "version": 1,
                "weight": 1,
                "reputation": 1,
            }
        ],
    )
    reputation_2 = (
        0.5,
        [
            {
                "name": "fake",
                "full_name": "fake",
                "description": "fake",
                "version": 1,
                "weight": 1,
                "reputation": 0.5,
            }
        ],
    )
    with mock.patch.object(
        teacher_reputation, "evaluate", return_value=reputation_1
    ):
        history_elem = ReputationHistory.create(teacher_reputation)
        assert history_elem.reputation.pk == teacher_reputation.pk
        assert history_elem.reputation_value == reputation_1[0]
        assert json.loads(history_elem.reputation_details) == reputation_1[1]
    with mock.patch.object(
        teacher_reputation, "evaluate", return_value=reputation_2
    ):

        history_elem = ReputationHistory.create(teacher_reputation)
        assert history_elem.reputation.pk == teacher_reputation.pk
        assert history_elem.reputation_value == reputation_2[0]
        assert json.loads(history_elem.reputation_details) == reputation_2[1]
