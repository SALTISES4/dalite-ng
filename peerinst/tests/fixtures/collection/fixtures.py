import pytest

from ..assignment import assignments  # noqa
from ..question import discipline  # noqa
from ..teacher import teachers  # noqa
from .generators import add_collections, new_collections


@pytest.fixture
def collection(teachers, assignments, discipline):
    return add_collections(
        new_collections(1, assignments, discipline, teachers)
    )[0]


@pytest.fixture
def collections(teachers, assignments, discipline):
    return add_collections(
        new_collections(2, assignments, discipline, teachers)
    )
