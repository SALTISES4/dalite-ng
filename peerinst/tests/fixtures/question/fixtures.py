import pytest

from . import factories as f
from ..teacher import teacher  # noqa
from .generators import (
    add_disciplines,
    add_questions,
    add_rationale_only_questions,
    new_disciplines,
    new_questions,
)


@pytest.fixture
def question(teacher):
    return add_questions(new_questions(1, teacher))[0]


@pytest.fixture
def questions(teacher):
    return add_questions(new_questions(10, teacher))


@pytest.fixture
def rationale_only_question():
    return add_rationale_only_questions(new_questions(1))[0]


@pytest.fixture
def rationale_only_questions():
    return add_rationale_only_questions(new_questions(2))


@pytest.fixture
def category():
    return f.CategoryFactory()


@pytest.fixture
def discipline():
    return add_disciplines(new_disciplines(1))[0]


@pytest.fixture
def disciplines():
    return add_disciplines(new_disciplines(2))
