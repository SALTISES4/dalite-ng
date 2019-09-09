import pytest
from django.core import exceptions

from dalite.models.custom_fields import ProbabilityField


def test_to_python():
    field = ProbabilityField()

    val = 1.0
    assert field.to_python(val) == val


def test_to_python__invalid_val():
    field = ProbabilityField()

    val = 1.1
    with pytest.raises(exceptions.ValidationError):
        field.to_python(val)

    val = -1.0
    with pytest.raises(exceptions.ValidationError):
        field.to_python(val)
