import random

from peerinst.models import Student, StudentAssignment

from .utils import add_to_group


def new_students(n):
    def generator():
        i = 0
        while True:
            i += 1
            yield {"email": f"test{i}@test.com"}

    gen = generator()
    return [next(gen) for _ in range(n)]


def new_student_assignments(n, group_assignments, students):
    group_assignments = (
        group_assignments
        if hasattr(group_assignments, "__iter__")
        else [group_assignments]
    )
    students = students if hasattr(students, "__iter__") else [students]

    def generator(combinations):
        while True:
            choice = random.choice(list(combinations))
            combinations = combinations - {choice}
            add_to_group(choice[0], choice[1].group)
            yield {"student": choice[0], "group_assignment": choice[1]}

    combinations = [
        (student, group) for group in group_assignments for student in students
    ]
    if n > len(combinations):
        raise ValueError("There aren't enough students and assignments")

    gen = generator(set(combinations))
    return [next(gen) for _ in range(n)]


def add_students(students):
    students = students if hasattr(students, "__iter__") else [students]
    return [Student.get_or_create(**s)[0] for s in students]


def add_student_assignments(student_assignments):
    student_assignments = (
        student_assignments
        if hasattr(student_assignments, "__iter__")
        else [student_assignments]
    )
    return [StudentAssignment.objects.create(**s) for s in student_assignments]
