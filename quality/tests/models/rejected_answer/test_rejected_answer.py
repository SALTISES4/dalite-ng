from quality.models import RejectedAnswer
from quality.tests.fixtures import *  # noqa


def test_add_and_dict(global_validation_quality):
    rationale = "random string"
    reasons = [{"a": 1, "b": 2}, {"c": 3, "d": 4}]

    bad_answer = RejectedAnswer.add(
        global_validation_quality, rationale, reasons
    )

    data = dict(bad_answer)
    assert data["rationale"] == rationale
    assert data["reasons"] == reasons
