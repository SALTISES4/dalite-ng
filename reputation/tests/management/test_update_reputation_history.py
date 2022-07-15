from unittest import mock

from django.core.management import call_command

from peerinst.tests.fixtures import *  # noqa
from reputation.models import ReputationHistory
from reputation.tests.fixtures import *  # noqa


def test_command(
    question_reputation, assignment_reputation, teacher_reputation
):
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

    n = ReputationHistory.objects.count()

    with mock.patch.object(
        question_reputation, "evaluate", return_value=reputation
    ), mock.patch.object(
        assignment_reputation, "evaluate", return_value=reputation
    ), mock.patch.object(
        teacher_reputation, "evaluate", return_value=reputation
    ):
        call_command("update_reputation_history")

        assert ReputationHistory.objects.count() == n + 3
