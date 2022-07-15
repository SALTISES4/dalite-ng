import pytest

from .generators import add_groups, new_groups


@pytest.fixture
def group():
    return add_groups(new_groups(1))[0]
