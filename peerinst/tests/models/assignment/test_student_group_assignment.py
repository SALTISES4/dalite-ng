import random
from datetime import datetime, timedelta
from operator import itemgetter

import pytest
import pytz
from django.core import mail

from peerinst.models import StudentAssignment, StudentGroupAssignment
from peerinst.tests.generators import (
    add_answers,
    add_student_group_assignments,
    add_to_group,
    new_student_group_assignments,
)

from .fixtures import *  # noqa F403


def test_new_student_group_assignment(group, assignment):
    data = new_student_group_assignments(1, group, assignment)[0]
    n_questions = assignment.questions.count()
    student_group_assignment = StudentGroupAssignment.objects.create(**data)
    assert isinstance(student_group_assignment, StudentGroupAssignment)
    assert student_group_assignment.group == data["group"]
    assert student_group_assignment.assignment == data["assignment"]
    assert student_group_assignment.order == ",".join(
        map(str, list(range(n_questions)))
    )


def test__modify_due_date(student_group_assignment):
    due_date = student_group_assignment.due_date
    new_due_date = datetime.now(pytz.utc) + timedelta(
        days=random.randint(1, 10)
    )
    data = {"due_date": (new_due_date).strftime("%Y-%m-%dT%H:%M:%S")}

    err = student_group_assignment._modify_due_date(**data)
    assert err is None
    assert abs(student_group_assignment.due_date - due_date) >= timedelta(
        seconds=1
    )
    assert abs(student_group_assignment.due_date - new_due_date) < timedelta(
        seconds=1
    )


def test__modify_due_date__with_floating_point(student_group_assignment):
    due_date = student_group_assignment.due_date
    new_due_date = datetime.now(pytz.utc) + timedelta(
        days=random.randint(1, 10)
    )
    data = {"due_date": (new_due_date).strftime("%Y-%m-%dT%H:%M:%S.%f")}

    err = student_group_assignment._modify_due_date(**data)
    assert err is None
    assert abs(student_group_assignment.due_date - due_date) >= timedelta(
        seconds=1
    )
    assert abs(student_group_assignment.due_date - new_due_date) < timedelta(
        seconds=1
    )


def test__modify_due_date__wrong_format(student_group_assignment):
    due_date = student_group_assignment.due_date
    new_due_date = datetime.now(pytz.utc) + timedelta(
        days=random.randint(1, 10)
    )
    data = {"due_date": (new_due_date).strftime("%Y/%m/%d %H-%M-%S.%f")}

    err = student_group_assignment._modify_due_date(**data)
    assert err == (
        'The given due date wasn\'t in the format "%Y-%m-%dT%H:%M:%S(.%f)?"'
    )
    assert abs(student_group_assignment.due_date - due_date) < timedelta(
        seconds=1
    )
    assert abs(new_due_date - student_group_assignment.due_date) >= timedelta(
        seconds=1
    )


def test__modify_order(student_group_assignment):
    k = student_group_assignment.assignment.questions.count()
    for _ in range(3):
        new_order = ",".join(map(str, random.sample(list(range(k)), k=k)))
        err = student_group_assignment._modify_order(new_order)
        assert err is None
        assert new_order == student_group_assignment.order


def test__modify_order__wrong_type(student_group_assignment):
    new_order = "abc"
    err = student_group_assignment._modify_order(new_order)
    assert err == "Given `order` isn't a comma separated list of integers."

    new_order = "a,b,c"
    err = student_group_assignment._modify_order(new_order)
    assert err == "Given `order` isn't a comma separated list of integers."


def test_get_question__by_idx(student_group_assignment):
    questions = student_group_assignment.questions
    for i, question in enumerate(questions):
        assert question == student_group_assignment.get_question(idx=i)


def test_get_question__regular(student_group_assignment):
    questions = student_group_assignment.questions
    for i, question in enumerate(questions):
        if i not in [0, len(questions) - 1]:
            assert (
                student_group_assignment.get_question(
                    current_question=question, after=True
                )
                == questions[i + 1]
            )

            assert (
                student_group_assignment.get_question(
                    current_question=question, after=False
                )
                == questions[i - 1]
            )


def test_get_question__edges(student_group_assignment):
    questions = student_group_assignment.questions
    assert (
        student_group_assignment.get_question(
            current_question=questions[0], after=False
        )
        is None
    )
    assert (
        student_group_assignment.get_question(
            current_question=questions[-1], after=True
        )
        is None
    )


def test_get_question__assert_raised(student_group_assignment):
    # To be revised with assertions in method
    #  with pytest.raises(AssertionError):
    #  student_group_assignment.get_question(
    #  0, student_group_assignment.questions[0]
    #  )
    pass


@pytest.mark.django_db(transaction=True)
def test_update_students(student_group_assignment, students):
    add_to_group(students, student_group_assignment.group)

    for student in students:
        assert not StudentAssignment.objects.filter(
            student=student, group_assignment=student_group_assignment
        ).exists()

    student_group_assignment.update_students()

    for student in students:
        assert StudentAssignment.objects.filter(
            student=student, group_assignment=student_group_assignment
        ).exists()

    assert len(mail.outbox) == len(students)


def test_update__due_date(student_group_assignment, students_with_assignment):
    data = {
        "name": "due_date",
        "value": datetime.now(pytz.utc).strftime("%Y-%m-%dT%H:%M:%S"),
    }

    err = student_group_assignment.update(**data)

    assert err is None
    assert len(mail.outbox) == len(students_with_assignment)


def test_update__question_list(
    student_group_assignment, students_with_assignment
):
    data = {
        "name": "question_list",
        "value": random.sample(
            [q.title for q in student_group_assignment.questions],
            len(student_group_assignment.questions),
        ),
    }

    err = student_group_assignment.update(**data)

    assert err is None
    assert len(mail.outbox) == len(students_with_assignment)


def test_update__wrong_name(student_group_assignment):
    data = {"name": "wrong_name", "value": None}

    err = student_group_assignment.update(**data)

    assert err == "An invalid name was sent."
    assert not mail.outbox


def test_check_reminder_status(
    student_group_assignment, students_with_assignment
):
    student_group_assignment.reminder_days = 3
    student_group_assignment.due_date = datetime.now(pytz.utc) + timedelta(
        days=2
    )
    student_group_assignment.save()

    err = student_group_assignment.check_reminder_status()

    assert err is None
    assert len(mail.outbox) == len(students_with_assignment)


def test_check_reminder_status__over_reminder_days(
    student_group_assignment, students_with_assignment
):
    student_group_assignment.reminder_days = 3
    student_group_assignment.due_date = datetime.now(pytz.utc) + timedelta(
        days=4
    )
    student_group_assignment.save()

    err = student_group_assignment.check_reminder_status()

    assert err is None
    assert not mail.outbox


def test_check_reminder_status__expired(
    student_group_assignment, students_with_assignment
):
    student_group_assignment.reminder_days = 3
    student_group_assignment.due_date = datetime.now(pytz.utc) + timedelta(
        days=-1
    )
    student_group_assignment.save()

    err = student_group_assignment.check_reminder_status()

    assert err is None
    assert not mail.outbox


def test_student_progress__no_questions_done(
    questions, students_with_assignment, student_group_assignment
):
    progress = student_group_assignment.student_progress

    assert not set(map(itemgetter("question_title"), progress)) - {
        q.title for q in questions
    }
    assert not {q.title for q in questions} - set(
        map(itemgetter("question_title"), progress)
    )

    for question in progress:
        assert question["n_students"] == len(students_with_assignment)
        assert question["n_completed"] == 0
        assert question["n_first_correct"] == 0
        assert question["n_correct"] == 0


def test_student_progress__some_first_answers_done(
    questions, students_with_assignment, student_group_assignment
):
    times_answered = {
        q.pk: random.randrange(1, len(students_with_assignment))
        for q in questions
    }
    n_correct = {
        q.pk: random.randint(0, times_answered[q.pk]) for q in questions
    }
    add_answers(
        [
            {
                "question": question,
                "assignment": student_group_assignment.assignment,
                "user_token": student.student.username,
                "first_answer_choice": 1 + (i >= n_correct[question.pk]),
                "rationale": "test",
            }
            for question in questions
            for i, student in enumerate(
                students_with_assignment[: times_answered[question.pk]]
            )
        ]
    )

    progress = student_group_assignment.student_progress

    assert not set(map(itemgetter("question_title"), progress)) - {
        q.title for q in questions
    }
    assert not {q.title for q in questions} - set(
        map(itemgetter("question_title"), progress)
    )

    for question in progress:
        question_ = next(
            q for q in questions if q.title == question["question_title"]
        )
        assert question["n_students"] == len(students_with_assignment)
        assert question["n_completed"] == 0
        assert question["n_first_correct"] == n_correct[question_.pk]
        assert question["n_correct"] == 0


def test_student_progress__all_first_answers_done(
    questions, students_with_assignment, student_group_assignment
):
    n_correct = {
        q.pk: random.randint(0, len(students_with_assignment))
        for q in questions
    }
    add_answers(
        [
            {
                "question": question,
                "assignment": student_group_assignment.assignment,
                "user_token": student.student.username,
                "first_answer_choice": 1 + (i >= n_correct[question.pk]),
                "rationale": "test",
            }
            for question in questions
            for i, student in enumerate(students_with_assignment)
        ]
    )

    progress = student_group_assignment.student_progress

    assert not set(map(itemgetter("question_title"), progress)) - {
        q.title for q in questions
    }
    assert not {q.title for q in questions} - set(
        map(itemgetter("question_title"), progress)
    )

    for question in progress:
        question_ = next(
            q for q in questions if q.title == question["question_title"]
        )
        assert question["n_students"] == len(students_with_assignment)
        assert question["n_completed"] == 0
        assert question["n_first_correct"] == n_correct[question_.pk]
        assert question["n_correct"] == 0


def test_student_progress__some_second_answers_done(
    questions, students_with_assignment, student_group_assignment
):
    times_first_answered = {
        q.pk: random.randrange(2, len(students_with_assignment))
        for q in questions
    }
    n_first_correct = {
        q.pk: random.randint(0, times_first_answered[q.pk]) for q in questions
    }
    times_second_answered = {
        q.pk: random.randrange(1, times_first_answered[q.pk])
        for q in questions
    }
    n_second_correct = {
        q.pk: random.randint(0, times_second_answered[q.pk]) for q in questions
    }
    answers = add_answers(
        [
            {
                "question": question,
                "assignment": student_group_assignment.assignment,
                "user_token": student.student.username,
                "first_answer_choice": 1
                + (
                    i + times_second_answered[question.pk]
                    >= n_first_correct[question.pk]
                ),
                "rationale": "test",
            }
            for question in questions
            for i, student in enumerate(
                students_with_assignment[
                    times_second_answered[question.pk] : times_first_answered[
                        question.pk
                    ]
                ]
            )
        ]
    )
    answers += add_answers(
        [
            {
                "question": question,
                "assignment": student_group_assignment.assignment,
                "user_token": student.student.username,
                "first_answer_choice": 1 + (i >= n_first_correct[question.pk]),
                "rationale": "test",
                "second_answer_choice": 1
                + (i >= n_second_correct[question.pk]),
                "chosen_rationale": random.choice(
                    [a for a in answers if a.question == question]
                ),
            }
            for question in questions
            for i, student in enumerate(
                students_with_assignment[: times_second_answered[question.pk]]
            )
        ]
    )

    progress = student_group_assignment.student_progress

    assert not set(map(itemgetter("question_title"), progress)) - {
        q.title for q in questions
    }
    assert not {q.title for q in questions} - set(
        map(itemgetter("question_title"), progress)
    )

    for question in progress:
        question_ = next(
            q for q in questions if q.title == question["question_title"]
        )
        assert question["n_students"] == len(students_with_assignment)
        assert question["n_completed"] == times_second_answered[question_.pk]
        assert question["n_first_correct"] == n_first_correct[question_.pk]
        assert question["n_correct"] == n_second_correct[question_.pk]


def test_student_progress__all_second_answers_done(
    questions, students_with_assignment, student_group_assignment
):
    n_first_correct = {
        q.pk: random.randint(0, len(students_with_assignment))
        for q in questions
    }
    n_second_correct = {
        q.pk: random.randint(0, len(students_with_assignment))
        for q in questions
    }
    add_answers(
        [
            {
                "question": question,
                "assignment": student_group_assignment.assignment,
                "user_token": student.student.username,
                "first_answer_choice": 1 + (i >= n_first_correct[question.pk]),
                "rationale": "test",
                "second_answer_choice": 1
                + (i >= n_second_correct[question.pk]),
                "chosen_rationale": None,
            }
            for question in questions
            for i, student in enumerate(students_with_assignment)
        ]
    )

    progress = student_group_assignment.student_progress

    assert not set(map(itemgetter("question_title"), progress)) - {
        q.title for q in questions
    }
    assert not {q.title for q in questions} - set(
        map(itemgetter("question_title"), progress)
    )

    for question in progress:
        question_ = next(
            q for q in questions if q.title == question["question_title"]
        )
        assert question["n_students"] == len(students_with_assignment)
        assert question["n_completed"] == len(students_with_assignment)
        assert question["n_first_correct"] == n_first_correct[question_.pk]
        assert question["n_correct"] == n_second_correct[question_.pk]


def test_student_progress__all_answers_correct_no_questions_all_answers_correct_done(  # noqa
    questions_all_answers_correct,
    students_with_assignment_all_answers_correct,
    student_group_assignment_all_answers_correct,
):
    progress = student_group_assignment_all_answers_correct.student_progress

    assert not set(map(itemgetter("question_title"), progress)) - {
        q.title for q in questions_all_answers_correct
    }
    assert not {q.title for q in questions_all_answers_correct} - set(
        map(itemgetter("question_title"), progress)
    )

    for question in progress:
        assert question["n_students"] == len(
            students_with_assignment_all_answers_correct
        )
        assert question["n_completed"] == 0
        assert question["n_first_correct"] == 0
        assert question["n_correct"] == 0


def test_student_progress__all_answers_correct_some_first_answers_done(
    questions_all_answers_correct,
    students_with_assignment_all_answers_correct,
    student_group_assignment_all_answers_correct,
):
    times_answered = {
        q.pk: random.randrange(
            1, len(students_with_assignment_all_answers_correct)
        )
        for q in questions_all_answers_correct
    }
    n_correct = {
        q.pk: random.randint(0, times_answered[q.pk])
        for q in questions_all_answers_correct
    }
    add_answers(
        [
            {
                "question": question,
                "assignment": student_group_assignment_all_answers_correct.assignment,  # noqa
                "user_token": student.student.username,
                "first_answer_choice": 1 + (i >= n_correct[question.pk]),
                "rationale": "test",
            }
            for question in questions_all_answers_correct
            for i, student in enumerate(
                students_with_assignment_all_answers_correct[
                    : times_answered[question.pk]
                ]
            )
        ]
    )

    progress = student_group_assignment_all_answers_correct.student_progress

    assert not set(map(itemgetter("question_title"), progress)) - {
        q.title for q in questions_all_answers_correct
    }
    assert not {q.title for q in questions_all_answers_correct} - set(
        map(itemgetter("question_title"), progress)
    )

    for question in progress:
        question_ = next(
            q
            for q in questions_all_answers_correct
            if q.title == question["question_title"]
        )
        assert question["n_students"] == len(
            students_with_assignment_all_answers_correct
        )
        assert question["n_completed"] == 0
        assert question["n_first_correct"] == times_answered[question_.pk]
        assert question["n_correct"] == 0


def test_student_progress__all_answers_correct_all_first_answers_done(
    questions_all_answers_correct,
    students_with_assignment_all_answers_correct,
    student_group_assignment_all_answers_correct,
):
    n_correct = {
        q.pk: random.randint(
            0, len(students_with_assignment_all_answers_correct)
        )
        for q in questions_all_answers_correct
    }
    add_answers(
        [
            {
                "question": question,
                "assignment": student_group_assignment_all_answers_correct.assignment,  # noqa
                "user_token": student.student.username,
                "first_answer_choice": 1 + (i >= n_correct[question.pk]),
                "rationale": "test",
            }
            for question in questions_all_answers_correct
            for i, student in enumerate(
                students_with_assignment_all_answers_correct
            )
        ]
    )

    progress = student_group_assignment_all_answers_correct.student_progress

    assert not set(map(itemgetter("question_title"), progress)) - {
        q.title for q in questions_all_answers_correct
    }
    assert not {q.title for q in questions_all_answers_correct} - set(
        map(itemgetter("question_title"), progress)
    )

    for question in progress:
        assert question["n_students"] == len(
            students_with_assignment_all_answers_correct
        )
        assert question["n_completed"] == 0
        assert question["n_first_correct"] == len(
            students_with_assignment_all_answers_correct
        )
        assert question["n_correct"] == 0


def test_student_progress__all_answers_correct_some_second_answers_done(
    questions_all_answers_correct,
    students_with_assignment_all_answers_correct,
    student_group_assignment_all_answers_correct,
):
    times_first_answered = {
        q.pk: random.randrange(
            2, len(students_with_assignment_all_answers_correct)
        )
        for q in questions_all_answers_correct
    }
    n_first_correct = {
        q.pk: random.randint(0, times_first_answered[q.pk])
        for q in questions_all_answers_correct
    }
    times_second_answered = {
        q.pk: random.randrange(1, times_first_answered[q.pk])
        for q in questions_all_answers_correct
    }
    n_second_correct = {
        q.pk: random.randint(0, times_second_answered[q.pk])
        for q in questions_all_answers_correct
    }
    answers = add_answers(
        [
            {
                "question": question,
                "assignment": student_group_assignment_all_answers_correct.assignment,  # noqa
                "user_token": student.student.username,
                "first_answer_choice": 1
                + (
                    i + times_second_answered[question.pk]
                    >= n_first_correct[question.pk]
                ),
                "rationale": "test",
            }
            for question in questions_all_answers_correct
            for i, student in enumerate(
                students_with_assignment_all_answers_correct[
                    times_second_answered[question.pk] : times_first_answered[
                        question.pk
                    ]
                ]
            )
        ]
    )
    answers += add_answers(
        [
            {
                "question": question,
                "assignment": student_group_assignment_all_answers_correct.assignment,  # noqa
                "user_token": student.student.username,
                "first_answer_choice": 1 + (i >= n_first_correct[question.pk]),
                "rationale": "test",
                "second_answer_choice": 1
                + (i >= n_second_correct[question.pk]),
                "chosen_rationale": random.choice(
                    [a for a in answers if a.question == question]
                ),
            }
            for question in questions_all_answers_correct
            for i, student in enumerate(
                students_with_assignment_all_answers_correct[
                    : times_second_answered[question.pk]
                ]
            )
        ]
    )

    progress = student_group_assignment_all_answers_correct.student_progress

    assert not set(map(itemgetter("question_title"), progress)) - {
        q.title for q in questions_all_answers_correct
    }
    assert not {q.title for q in questions_all_answers_correct} - set(
        map(itemgetter("question_title"), progress)
    )

    for question in progress:
        question_ = next(
            q
            for q in questions_all_answers_correct
            if q.title == question["question_title"]
        )
        assert question["n_students"] == len(
            students_with_assignment_all_answers_correct
        )
        assert question["n_completed"] == times_second_answered[question_.pk]
        assert (
            question["n_first_correct"] == times_first_answered[question_.pk]
        )
        assert question["n_correct"] == times_second_answered[question_.pk]


def test_student_progress__all_answers_correct_all_second_answers_done(
    questions_all_answers_correct,
    students_with_assignment_all_answers_correct,
    student_group_assignment_all_answers_correct,
):
    n_first_correct = {
        q.pk: random.randint(
            0, len(students_with_assignment_all_answers_correct)
        )
        for q in questions_all_answers_correct
    }
    n_second_correct = {
        q.pk: random.randint(
            0, len(students_with_assignment_all_answers_correct)
        )
        for q in questions_all_answers_correct
    }
    add_answers(
        [
            {
                "question": question,
                "assignment": student_group_assignment_all_answers_correct.assignment,  # noqa
                "user_token": student.student.username,
                "first_answer_choice": 1 + (i >= n_first_correct[question.pk]),
                "rationale": "test",
                "second_answer_choice": 1
                + (i >= n_second_correct[question.pk]),
                "chosen_rationale": None,
            }
            for question in questions_all_answers_correct
            for i, student in enumerate(
                students_with_assignment_all_answers_correct
            )
        ]
    )

    progress = student_group_assignment_all_answers_correct.student_progress

    assert not set(map(itemgetter("question_title"), progress)) - {
        q.title for q in questions_all_answers_correct
    }
    assert not {q.title for q in questions_all_answers_correct} - set(
        map(itemgetter("question_title"), progress)
    )

    for question in progress:
        assert question["n_students"] == len(
            students_with_assignment_all_answers_correct
        )
        assert question["n_completed"] == len(
            students_with_assignment_all_answers_correct
        )
        assert question["n_first_correct"] == len(
            students_with_assignment_all_answers_correct
        )
        assert question["n_correct"] == len(
            students_with_assignment_all_answers_correct
        )


def test_hashing(student_group_assignment):
    assert student_group_assignment == StudentGroupAssignment.get(
        student_group_assignment.hash
    )


def test_expired__expired(group, assignment):
    student_group_assignment = add_student_group_assignments(
        new_student_group_assignments(
            1, group, assignment, due_date=datetime.now(pytz.utc)
        )
    )[0]
    assert student_group_assignment.expired


def test_expired__not_expired(group, assignment):
    student_group_assignment = add_student_group_assignments(
        new_student_group_assignments(
            1,
            group,
            assignment,
            due_date=datetime.now(pytz.utc) + timedelta(days=1),
        )
    )[0]
    assert not student_group_assignment.expired


def test_questions(student_group_assignment):
    k = len(student_group_assignment.questions)
    new_order = ",".join(map(str, random.sample(list(range(k)), k=k)))
    err = student_group_assignment._modify_order(new_order)
    assert err is None
    for i, j in enumerate(map(int, new_order.split(","))):
        assert (
            student_group_assignment.questions[i]
            == student_group_assignment.assignment.questions.all()[j]
        )

    assert new_order == student_group_assignment.order
