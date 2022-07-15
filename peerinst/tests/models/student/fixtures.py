import pytest

from peerinst.tests.generators import (
    add_answer_choices,
    add_assignments,
    add_groups,
    add_questions,
    add_student_assignments,
    add_student_group_assignments,
    add_students,
    add_to_group,
    new_assignments,
    new_groups,
    new_questions,
    new_student_assignments,
    new_student_group_assignments,
    new_students,
)


@pytest.fixture
def student():
    return add_students(new_students(1))[0]


@pytest.fixture
def group():
    return add_groups(new_groups(1))[0]


@pytest.fixture
def questions():
    questions = add_questions(new_questions(10))
    add_answer_choices(2, questions)
    return questions


@pytest.fixture
def assignment(questions):
    return add_assignments(
        new_assignments(1, questions, min_questions=len(questions))
    )[0]


@pytest.fixture
def group_assignment(group, assignment):
    return add_student_group_assignments(
        new_student_group_assignments(1, group, assignment)
    )[0]


@pytest.fixture
def student_assignment(student, group_assignment):
    add_to_group(student, group_assignment.group)
    return add_student_assignments(
        new_student_assignments(1, group_assignment, student)
    )[0]
