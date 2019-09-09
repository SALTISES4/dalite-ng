import pytest

from ..assignment import student_group_assignment  # noqa
from ..assignment import student_group_assignments  # noqa
from ..tos import consent_to_tos, tos_student  # noqa
from .generators import (
    add_student_assignments,
    add_students,
    new_student_assignments,
    new_students,
)


@pytest.fixture
def student(tos_student):
    student = add_students(new_students(1))[0]
    student.student.is_active = True
    student.student.save()
    consent_to_tos(student, tos_student)
    return student


@pytest.fixture
def students(tos_student):
    students = add_students(new_students(10))
    for student in students:
        student.student.is_active = True
        student.student.save()
        consent_to_tos(student, tos_student)
    return students


@pytest.fixture
def student_new(tos_student):
    student = add_students(new_students(1))[0]
    return student


@pytest.fixture
def student_assignment(student, student_group_assignment):
    return add_student_assignments(
        new_student_assignments(1, student_group_assignment, student)
    )[0]


@pytest.fixture
def student_assignments(students, student_group_assignments):
    return add_student_assignments(
        new_student_assignments(
            len(students) * len(student_group_assignments),
            student_group_assignments,
            students,
        )
    )
