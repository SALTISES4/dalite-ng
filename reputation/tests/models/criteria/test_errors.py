import pytest

from reputation.models.criteria.errors import CriterionDoesNotExistError


def test_criterion_does_not_exists__no_msg():
    with pytest.raises(CriterionDoesNotExistError) as e:
        raise CriterionDoesNotExistError()
    assert (
        "There is no criterion corresponding to that name or version."
        in str(e.value)
    )


def test_criterion_does_not_exists__msg():
    msg = "error msg"
    with pytest.raises(CriterionDoesNotExistError) as e:
        raise CriterionDoesNotExistError(msg)
    assert msg in str(e.value)
