from __future__ import unicode_literals

import random
import string
from datetime import datetime, timedelta

import pytz
from django.contrib.auth.models import User

from peerinst.models import (
    Answer,
    Assignment,
    Question,
    Student,
    StudentAssignment,
    StudentGroup,
    StudentGroupAssignment,
    Teacher,
)
from tos.models import Consent as TosConsent


def new_answers(n, assignments):
    if n > sum(
        len(a.group_assignment.assignment.questions.all()) for a in assignments
    ):
        raise RuntimeError("There aren't enough questions in the assignments")
    answers = []
    current = {
        i: 0 if len(a.group_assignment.assignment.questions.all()) else None
        for i, a in enumerate(assignments)
    }
    while len(answers) < n:
        i = random.choice([k for k, v in current.items() if v is not None])
        answers.append(
            {
                "question": assignments[
                    i
                ].group_assignment.assignment.questions.all()[current[i]],
                "assignment": assignments[i].group_assignment.assignment,
                "user_token": assignments[i].student.student.username,
                "first_answer_choice": random.randint(0, 5),
                "rationale": "".join(
                    random.choice(string.ascii_letters) for _ in range(100)
                ),
            }
        )
        current[i] += 1
        if current[i] >= len(
            assignments[i].group_assignment.assignment.questions.all()
        ):
            current[i] = None

    return answers


def new_assignments(n, questions, min_questions=1):
    def generator(min_questions):
        chars = string.ascii_letters + string.digits + "_-."
        gen = _extra_chars_gen()
        while True:
            yield {
                "identifier": "{}{}".format(
                    "".join(
                        random.choice(chars)
                        for _ in range(random.randint(1, 50))
                    ),
                    next(gen),
                ),
                "title": "{}{}".format(
                    "".join(
                        random.choice(chars)
                        for _ in range(random.randint(1, 50))
                    ),
                    next(gen),
                ),
                "questions": random.sample(
                    questions, k=random.randint(min_questions, len(questions))
                ),
            }

    gen = generator(min_questions)
    return [next(gen) for _ in range(n)]


def new_groups(n):
    def generator():
        chars = string.ascii_letters + string.digits + "_-."
        gen = _extra_chars_gen()
        while True:
            yield {
                "name": "{}{}".format(
                    "".join(
                        random.choice(chars)
                        for _ in range(random.randint(1, 50))
                    ),
                    next(gen),
                ),
                "title": "".join(
                    random.choice(chars) for _ in range(random.randint(1, 50))
                ),
            }

    gen = generator()
    return [next(gen) for _ in range(n)]


def new_questions(n):
    def generator():
        chars = string.ascii_letters + string.digits + "_-."
        gen = _extra_chars_gen()
        while True:
            yield {
                "title": "{}{}".format(
                    "".join(random.choice(chars) for _ in range(4)), next(gen)
                ),
                "text": "".join(
                    random.choice(chars) for _ in range(random.randint(1, 100))
                ),
            }

    gen = generator()
    return [next(gen) for _ in range(n)]


def new_students(n):
    def generator():
        chars = string.ascii_lowercase + string.digits + "_-."
        gen = _extra_chars_gen()
        while True:
            yield {
                "email": "{}{}@{}.{}".format(
                    "".join(
                        random.choice(chars)
                        for _ in range(random.randint(1, 32))
                    ),
                    next(gen),
                    "".join(
                        random.choice(chars)
                        for _ in range(random.randint(1, 10))
                    ),
                    "".join(
                        random.choice(chars)
                        for _ in range(random.randint(2, 3))
                    ),
                )
            }

    gen = generator()
    return [next(gen) for _ in range(n)]


def new_student_assignments(n, group_assignments, students):
    def generator(combinations):
        choice = random.choice(list(combinations))
        combinations = combinations - set(choice)
        while True:
            yield {"student": choice[0], "group_assignment": choice[1]}

    combinations = [
        (student, group) for group in group_assignments for student in students
    ]
    if n > len(combinations):
        raise ValueError("There aren't enough students and assignments")

    gen = generator(set(combinations))
    return [next(gen) for _ in range(n)]


def new_student_group_assignments(n, groups, assignments, due_date=None):
    def generator(groups, assignments, due_date):
        while True:
            if due_date is None:
                if random.random() > 0.5:
                    due_date = datetime.now(pytz.utc) + timedelta(
                        days=random.randint(1, 60)
                    )
                else:
                    due_date = None
            yield {
                "group": random.choice(groups),
                "assignment": random.choice(assignments),
                "due_date": due_date,
            }

    gen = generator(groups, assignments, due_date)
    return [next(gen) for _ in range(n)]


def new_users(n):
    def generator():
        chars = string.ascii_letters + string.digits + "_-."
        gen = _extra_chars_gen()
        while True:
            yield {
                "username": "{}{}".format(
                    "".join(
                        random.choice(chars)
                        for _ in range(random.randint(1, 12))
                    ),
                    next(gen),
                ),
                "email": "{}@{}.{}".format(
                    "".join(
                        random.choice(chars)
                        for _ in range(random.randint(1, 32))
                    ),
                    "".join(
                        random.choice(chars)
                        for _ in range(random.randint(1, 10))
                    ),
                    "".join(
                        random.choice(chars)
                        for _ in range(random.randint(2, 3))
                    ),
                ),
                "password": "test",
            }

    gen = generator()
    return [next(gen) for _ in range(n)]


def add_answers(answers):
    return [Answer.objects.create(**a) for a in answers]


def add_assignments(assignments):
    assignments_ = [
        Assignment.objects.create(
            **{k: v for k, v in a.items() if k != "questions"}
        )
        for a in assignments
    ]
    for assignment, a in zip(assignments_, assignments):
        assignment.questions.add(*a["questions"])
    return assignments_


def add_groups(groups):
    return [StudentGroup.objects.create(**g) for g in groups]


def add_questions(questions):
    return [Question.objects.create(**q) for q in questions]


def add_students(students):
    return [Student.get_or_create(**s) for s in students]


def add_student_assignments(student_assignments):
    return [StudentAssignment.objects.create(**s) for s in student_assignments]


def add_student_group_assignments(group_assignments):
    return [
        StudentGroupAssignment.objects.create(**g) for g in group_assignments
    ]


def add_users(users):
    return [User.objects.create_user(**u) for u in users]


def add_second_choice_to_answers(answers, assignment, n_second_choices=None):
    assignments = set((a.assignment for a in answers))
    answers_ = [
        a
        for a in answers
        if a.assignment == assignment.group_assignment.assignment
        and a.user_token == assignment.student.student.username
    ]
    for i in range(n_second_choices or random.randrange(1, len(answers_))):
        answers_[i].chosen_rationale = random.choice(answers_)
        answers_[i].second_answer_choice = answers_[
            i
        ].chosen_rationale.first_answer_choice
        answers_[i].save()
    return answers


def _extra_chars_gen():
    letters = string.ascii_letters
    indices = [0]
    while True:
        yield "".join(letters[i] for i in indices)
        for i in range(len(indices)):
            if indices[i] < len(letters) - 1:
                indices[i] += 1
                break
            else:
                if i == len(indices) - 1:
                    indices = [0] * len(indices)
                    indices.append(0)
                    break
