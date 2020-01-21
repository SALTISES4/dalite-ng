import random
from datetime import datetime, timedelta

import pytz

from peerinst.models import Assignment, StudentGroupAssignment


def new_assignments(n, questions, min_questions=1):
    questions = [questions] if not isinstance(questions, list) else questions

    def generator(min_questions):
        i = 0
        while True:
            i += 1
            yield {
                "identifier": "assignment{}".format(i),
                "title": "assignment{}".format(i),
                "questions": random.sample(
                    questions, k=random.randint(min_questions, len(questions))
                ),
            }

    gen = generator(min_questions)
    return [next(gen) for _ in range(n)]


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


def new_student_group_assignments(n, groups, assignments, due_date=None):
    groups = [groups] if not isinstance(groups, list) else groups
    assignments = (
        [assignments] if not isinstance(assignments, list) else assignments
    )

    def generator(groups, assignments, due_date):
        while True:
            if due_date is None:
                due_date = datetime.now(pytz.utc) + timedelta(
                    days=random.randint(1, 6)
                )
            yield {
                "group": random.choice(groups),
                "assignment": random.choice(assignments),
                "due_date": due_date,
                "distribution_date": datetime.now(pytz.utc)
                - timedelta(days=random.randint(1, 6)),
            }

    gen = generator(groups, assignments, due_date)
    return [next(gen) for _ in range(n)]


def add_student_group_assignments(group_assignments):
    return [
        StudentGroupAssignment.objects.create(**g) for g in group_assignments
    ]
