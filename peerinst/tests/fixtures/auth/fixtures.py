import pytest

from .generators import add_users, new_users


@pytest.fixture
def user():
    return add_users(new_users(1))[0]
