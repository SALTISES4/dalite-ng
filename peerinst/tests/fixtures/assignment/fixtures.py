import pytest

from ..group import group  # noqa
from ..question import questions  # noqa
from .generators import (
    add_assignments,
    add_student_group_assignments,
    new_assignments,
    new_student_group_assignments,
)


@pytest.fixture
def assignment(questions):
    return add_assignments(
        new_assignments(1, questions, min_questions=len(questions))
    )[0]


@pytest.fixture
def assignments(questions):
    return add_assignments(
        new_assignments(2, questions, min_questions=len(questions))
    )


@pytest.fixture
def student_group_assignment(assignment, group):
    return add_student_group_assignments(
        new_student_group_assignments(1, group, assignment)
    )[0]


@pytest.fixture
def student_group_assignments(assignments, group):
    return [
        add_student_group_assignments(
            new_student_group_assignments(1, group, assignment)
        )[0]
        for assignment in assignments
    ]
