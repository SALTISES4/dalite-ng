import pytest

from peerinst.tests.generators import (
    add_answer_choices,
    add_answers,
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
def questions():
    questions = add_questions(new_questions(20))
    add_answer_choices(2, questions)
    return questions


@pytest.fixture()
def groups():
    return add_groups(new_groups(3))


@pytest.fixture
def assignments(questions):
    return add_assignments(new_assignments(3, questions, min_questions=5))


@pytest.fixture
def student_group_assignments(groups, assignments):
    return add_student_group_assignments(
        new_student_group_assignments(
            len(groups) * len(assignments), groups, assignments
        )
    )


@pytest.fixture
def students_with_assignments(student_group_assignments):
    students = add_students(new_students(20))
    add_to_group(students, [a.group for a in student_group_assignments])
    add_student_assignments(
        new_student_assignments(
            len(students) * len(student_group_assignments),
            student_group_assignments,
            students,
        )
    )
    return students
