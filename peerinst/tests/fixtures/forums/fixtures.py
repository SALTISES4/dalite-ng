import pytest

from ..teacher import teachers  # noqa
from .generators import add_forum, add_threads, new_forum, new_threads


@pytest.fixture
def forum():
    return add_forum(new_forum())


@pytest.fixture
def thread(teachers, forum):
    return add_threads(new_threads(1, forum, teachers, 20), teachers)[0]


@pytest.fixture
def threads(teachers, forum):
    return add_threads(new_threads(3, forum, teachers, 20), teachers)
