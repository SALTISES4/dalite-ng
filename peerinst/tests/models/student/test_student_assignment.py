import random
from datetime import datetime, timedelta

import pytz
from django.core import mail

from peerinst.models import (
    StudentAssignment,
    StudentGroupMembership,
    StudentNotification,
)
from peerinst.tests.fixtures.student.generators import new_student_assignments
from peerinst.tests.fixtures import add_answers
from peerinst.models import Assignment


def test_new_student_assignment(student, student_group_assignment):
    data = new_student_assignments(1, student_group_assignment, student)[0]

    assignment = StudentAssignment.objects.create(**data)
    assert isinstance(assignment, StudentAssignment)
    assert assignment.student == student
    assert assignment.group_assignment == student_group_assignment


def test_send_email__new_assignment(student_assignment):
    err = student_assignment.send_email(mail_type="new_assignment")

    assert err is None
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "New assignment for group {}".format(
        student_assignment.group_assignment.group.title
    )


def test_send_email__new_assignment_with_localhost(student_assignment):
    student_assignment.student.student.email = "fake-email@localhost"
    student_assignment.student.student.save()

    err = student_assignment.send_email(mail_type="new_assignment")

    assert err is None
    assert not mail.outbox


def test_send_email__assignment_updated(student_assignment):
    err = student_assignment.send_email(mail_type="assignment_updated")

    assert err is None
    assert len(mail.outbox) == 1
    assert mail.outbox[
        0
    ].subject == "Assignment {} for group {} updated".format(
        student_assignment.group_assignment.assignment.title,
        student_assignment.group_assignment.group.title,
    )


def test_send_email__assignment_updated_with_localhost(student_assignment):
    student_assignment.student.student.email = "fake-email@localhost"
    student_assignment.student.student.save()

    err = student_assignment.send_email(mail_type="assignment_updated")

    assert err is None
    assert not mail.outbox


def test_send_email__assignment_about_to_expire(student_assignment):
    student_assignment.group_assignment.due_date = datetime.now(
        pytz.utc
    ) + timedelta(days=2)
    student_assignment.group_assignment.save()
    err = student_assignment.send_email(mail_type="assignment_about_to_expire")

    assert err is None
    assert len(mail.outbox) == 1
    assert mail.outbox[
        0
    ].subject == "Assignment {} for group {} expires in {} days".format(
        student_assignment.group_assignment.assignment.title,
        student_assignment.group_assignment.group.title,
        student_assignment.group_assignment.days_to_expiry,
    )


def test_send_email__assignment_about_to_expire_in_0_days(student_assignment):
    student_assignment.group_assignment.due_date = datetime.now(
        pytz.utc
    ) + timedelta(hours=12)
    student_assignment.group_assignment.save()
    err = student_assignment.send_email(mail_type="assignment_about_to_expire")

    assert err is None
    assert len(mail.outbox) == 1
    assert mail.outbox[
        0
    ].subject == "Assignment {} for group {} expires today".format(
        student_assignment.group_assignment.assignment.title,
        student_assignment.group_assignment.group.title,
        student_assignment.group_assignment.days_to_expiry,
    )


def test_send_email__assignment_about_to_expire_with_localhost(
    student_assignment,
):
    student_assignment.student.student.email = "fake-email@localhost"
    student_assignment.student.student.save()

    err = student_assignment.send_email(mail_type="assignment_about_to_expire")

    assert err is None
    assert not mail.outbox


def test_send_email__wrong_type(student_assignment):
    err = student_assignment.send_email(mail_type="wrong_type")

    assert err == "The `mail_type` wasn't in the allowed types."
    assert not mail.outbox


def test_send_email__no_email(student_assignment):
    student_assignment.student.student.email = ""
    student_assignment.student.student.save()

    err = student_assignment.send_email(mail_type="new_assignment")

    assert err == "There is no email associated with user {}.".format(
        student_assignment.student.student.username
    )
    assert not mail.outbox


def test_get_current_question__no_answers(student_assignment):
    questions = student_assignment.group_assignment.questions

    question = student_assignment.get_current_question()
    assert question == questions[0]

    for _ in range(5):
        new_order = ",".join(
            map(str, random.sample(range(len(questions)), k=len(questions)))
        )
        student_assignment.group_assignment._modify_order(new_order)
        questions = student_assignment.group_assignment.questions
        question = student_assignment.get_current_question()
        assert question == questions[0]


def test_get_current_question__some_first_answers_done(student_assignment):
    student = student_assignment.student
    questions = student_assignment.group_assignment.questions
    n_done = random.randrange(1, len(questions))

    add_answers(
        student,
        questions[:n_done],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=False,
    )

    question = student_assignment.get_current_question()
    assert question == questions[n_done]


def test_get_current_question__all_first_answers_done(student_assignment):
    student = student_assignment.student
    questions = student_assignment.group_assignment.questions

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=False,
    )

    question = student_assignment.get_current_question()
    assert question == questions[0]


def test_get_current_question__some_second_answers_done(student_assignment):
    student = student_assignment.student
    questions = student_assignment.group_assignment.questions
    n_second = random.randrange(1, len(questions))

    add_answers(
        student,
        questions[n_second:],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=False,
    )
    add_answers(
        student,
        questions[:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )

    question = student_assignment.get_current_question()
    assert question == questions[n_second]


def test_get_current_question__all_second_answers_done(student_assignment):
    student = student_assignment.student
    questions = student_assignment.group_assignment.questions

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )

    question = student_assignment.get_current_question()
    assert question is None


def test_send_reminder(student_assignment):
    assert not student_assignment.reminder_sent
    assert not student_assignment.completed
    assert not StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()

    student_assignment.send_reminder(last_day=False)

    assert StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()
    assert student_assignment.reminder_sent
    assert len(mail.outbox) == 1


def test_send_reminder__reminder_sent(student_assignment):
    student_assignment.reminder_sent = True
    student_assignment.save()

    assert student_assignment.reminder_sent
    assert not student_assignment.completed
    assert not StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()

    student_assignment.send_reminder(last_day=False)

    assert StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()
    assert student_assignment.reminder_sent
    assert not mail.outbox


def test_send_reminder__reminder_sent_send_every_day(student_assignment):
    student_assignment.reminder_sent = True
    student_assignment.student.send_reminder_email_every_day = True
    student_assignment.student.save()

    assert student_assignment.reminder_sent
    assert not student_assignment.completed
    assert not StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()

    student_assignment.send_reminder(last_day=False)

    assert StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()
    assert student_assignment.reminder_sent
    assert len(mail.outbox) == 1


def test_send_reminder__reminder_sent_send_day_before(student_assignment):
    student_assignment.reminder_sent = True
    student_assignment.send_reminder_email_day_before = True
    student_assignment.save()

    assert student_assignment.reminder_sent
    assert not student_assignment.completed
    assert not StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()

    student_assignment.send_reminder(last_day=False)

    assert StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()
    assert student_assignment.reminder_sent
    assert not mail.outbox


def test_send_reminder__reminder_sent_send_day_before_last_day(
    student_assignment,
):
    student_assignment.reminder_sent = True
    student_assignment.send_reminder_email_day_before = True
    student_assignment.save()

    assert student_assignment.reminder_sent
    assert not student_assignment.completed
    assert not StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()

    student_assignment.send_reminder(last_day=True)

    assert StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()
    assert student_assignment.reminder_sent
    assert len(mail.outbox) == 1


def test_send_reminder__reminder_sent_send_every_day_and_day_before_last_day(
    student_assignment,
):
    student_assignment.reminder_sent = True
    student_assignment.save()
    student_assignment.student.send_reminder_email_every_day = True
    student_assignment.student.send_reminder_email_day_before = True
    student_assignment.student.save()

    assert student_assignment.reminder_sent
    assert not student_assignment.completed
    assert not StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()

    student_assignment.send_reminder(last_day=True)

    assert StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()
    assert student_assignment.reminder_sent
    assert len(mail.outbox) == 1


def test_send_reminder__completed(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )

    assert not student_assignment.reminder_sent
    assert student_assignment.completed
    assert not StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()

    student_assignment.send_reminder(last_day=False)

    assert not StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()
    assert not student_assignment.reminder_sent
    assert not mail.outbox


def test_send_reminder__no_email_sending(student_assignment):
    membership = StudentGroupMembership.objects.get(
        student=student_assignment.student,
        group=student_assignment.group_assignment.group,
    )
    membership.send_emails = False
    membership.save()

    assert not student_assignment.reminder_sent
    assert not student_assignment.completed
    assert not StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()

    student_assignment.send_reminder(last_day=False)

    assert StudentNotification.objects.filter(
        student=student_assignment.student,
        notification__type="assignment_about_to_expire",
    ).exists()
    assert not student_assignment.reminder_sent
    assert not mail.outbox


def test_completed__no_answers(student_assignment):
    assert not student_assignment.completed


def test_completed__some_first_answers(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)

    add_answers(
        student,
        questions[:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=False,
    )

    assert not student_assignment.completed


def test_completed__some_first_and_second_answers(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)

    add_answers(
        student,
        questions[:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )
    add_answers(
        student,
        questions[n_second:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=False,
    )

    assert not student_assignment.completed


def test_completed__all_first_and_some_second_answers(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_second = random.randint(1, n - 1)

    add_answers(
        student,
        questions[n_second:],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=False,
    )
    add_answers(
        student,
        questions[:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )

    assert not student_assignment.completed


def test_completed__all_first_and_second_answers(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )

    assert student_assignment.completed


def test_completed__multiple_same_assignment(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )

    assert student_assignment.completed

    assignment_clone = Assignment.objects.create(
        identifier="__test__", title=assignment.title
    )
    for question in questions:
        assignment_clone.questions.add(question)

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=False,
    )

    assert not student_assignment.completed


def test_results__no_answers(student_assignment):
    n = student_assignment.group_assignment.assignment.questions.count()

    correct = {
        "n_completed": 0,
        "n_first_correct": 0,
        "n_correct": 0,
        "n": n,
        "grade": 0,
    }

    result = student_assignment.results
    assert result == correct


def test_results__all_answered_correct(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )

    correct = {
        "n_completed": n,
        "n_first_correct": n,
        "n_correct": n,
        "n": n,
        "grade": n,
    }

    result = student_assignment.results
    assert result == correct


def test_results__some_answered_correct_second(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_second = random.randint(1, n - 1)
    n_correct_second = random.randint(1, n_second)

    add_answers(
        student,
        questions[n_second:],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=False,
    )
    add_answers(
        student,
        questions[:n_correct_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=True,
    )
    add_answers(
        student,
        questions[n_correct_second:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
    )

    correct = {
        "n_completed": n_second,
        "n_first_correct": 0,
        "n_correct": n_correct_second,
        "n": n,
        "grade": float(n_correct_second) / 2,
    }

    result = student_assignment.results
    assert result == correct


def test_results__some_answered_correct_first_and_second(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(4, n - 1)
    n_second = random.randint(3, n_first)
    n_correct_first = random.randint(2, n_second)
    n_correct_second = random.randint(1, n_correct_first)

    add_answers(
        student,
        questions[:n_correct_second],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )
    add_answers(
        student,
        questions[n_correct_second:n_correct_first],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_correct_first:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_second:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=False,
    )

    correct = {
        "n_completed": n_second,
        "n_first_correct": n_correct_first,
        "n_correct": n_correct_second,
        "n": n,
        "grade": n_correct_second + 0.5 * (n_correct_first - n_correct_second),
    }

    result = student_assignment.results
    assert result == correct


def test_results__all_answered_correct_first_and_none_second(
    student_assignment,
):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)

    add_answers(
        student,
        questions[:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_second:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=False,
    )

    correct = {
        "n_completed": n_second,
        "n_first_correct": n_first,
        "n_correct": 0,
        "n": n,
        "grade": float(n_first) / 2,
    }

    result = student_assignment.results
    assert result == correct


def test_results__none_answered_correct_first_and_all_second(
    student_assignment,
):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)

    add_answers(
        student,
        questions[:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=True,
    )
    add_answers(
        student,
        questions[n_second:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=False,
    )

    correct = {
        "n_completed": n_second,
        "n_first_correct": 0,
        "n_correct": n_second,
        "n": n,
        "grade": float(n_second) / 2,
    }

    result = student_assignment.results
    assert result == correct


def test_results__none_answered_correct_first_and_second(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)

    add_answers(
        student,
        questions[:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_second:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=False,
    )

    correct = {
        "n_completed": n_second,
        "n_first_correct": 0,
        "n_correct": 0,
        "n": n,
        "grade": 0,
    }

    result = student_assignment.results
    assert result == correct


def test_grade__no_answers(student_assignment):
    assert not student_assignment.grade


def test_grade__all_answered_correct(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )

    assert student_assignment.grade == n


def test_grade__some_answered_correct_second(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_second = random.randint(1, n - 1)
    n_correct_second = random.randint(1, n_second)

    add_answers(
        student,
        questions[:n_correct_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=True,
    )
    add_answers(
        student,
        questions[n_correct_second:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_second:],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=False,
    )

    assert student_assignment.grade == float(n_correct_second) / 2


def test_grade__some_answered_correct_first_and_second(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(4, n - 1)
    n_second = random.randint(3, n_first)
    n_correct_first = random.randint(2, n_second)
    n_correct_second = random.randint(1, n_correct_first)

    add_answers(
        student,
        questions[:n_correct_second],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )
    add_answers(
        student,
        questions[n_correct_second:n_correct_first],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_correct_second:n_correct_first],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_correct_first:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_second:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=False,
    )

    assert student_assignment.grade == n_correct_second + 0.5 * (
        n_correct_first - n_correct_second
    )


def test_grade__all_answered_correct_first_and_none_second(
    student_assignment,
):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)

    add_answers(
        student,
        questions[:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_second:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=False,
    )

    assert student_assignment.grade == float(n_first) / 2


def test_grade__none_answered_correct_first_and_all_second(
    student_assignment,
):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)

    add_answers(
        student,
        questions[:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=True,
    )
    add_answers(
        student,
        questions[n_second:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=False,
    )

    assert student_assignment.grade == float(n_second) / 2


def test_grade__none_answered_correct_first_and_second(student_assignment):
    print(student_assignment.group_assignment.distribution_date)
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)

    add_answers(
        student,
        questions[:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_second:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=False,
    )


def test_grade__other_assignments__no_answers(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    now = datetime.now(pytz.utc)
    old_datetime = now - timedelta(weeks=2)
    new_datetime = now + timedelta(weeks=2)
    student_assignment.group_assignment.due_date = now + timedelta(weeks=1)
    student_assignment.group_assignment.distribution_date = now - timedelta(
        weeks=1
    )
    student_assignment.group_assignment.save()

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=old_datetime,
    )
    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=new_datetime,
    )

    assert not student_assignment.grade


def test_grade__other_assignments__all_answered_correct(student_assignment):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    now = datetime.now(pytz.utc)
    old_datetime = now - timedelta(weeks=2)
    new_datetime = now + timedelta(weeks=2)
    student_assignment.group_assignment.due_date = now + timedelta(weeks=1)
    student_assignment.group_assignment.distribution_date = now - timedelta(
        weeks=1
    )
    student_assignment.group_assignment.save()

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
        datetime_start=old_datetime,
    )
    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
        datetime_start=new_datetime,
    )

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )

    assert student_assignment.grade == n


def test_grade__other_assignments__some_answered_correct_second(
    student_assignment,
):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_second = random.randint(1, n - 1)
    n_correct_second = random.randint(1, n_second)
    now = datetime.now(pytz.utc)
    old_datetime = now - timedelta(weeks=2)
    new_datetime = now + timedelta(weeks=2)
    student_assignment.group_assignment.due_date = now + timedelta(weeks=1)
    student_assignment.group_assignment.distribution_date = now - timedelta(
        weeks=1
    )
    student_assignment.group_assignment.save()

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=old_datetime,
    )
    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=new_datetime,
    )

    add_answers(
        student,
        questions[:n_correct_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=True,
    )
    add_answers(
        student,
        questions[n_correct_second:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_second:],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=False,
    )

    assert student_assignment.grade == float(n_correct_second) / 2


def test_grade__other_assignments__some_answered_correct_first_and_second(
    student_assignment,
):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(4, n - 1)
    n_second = random.randint(3, n_first)
    n_correct_first = random.randint(2, n_second)
    n_correct_second = random.randint(1, n_correct_first)
    now = datetime.now(pytz.utc)
    old_datetime = now - timedelta(weeks=2)
    new_datetime = now + timedelta(weeks=2)
    student_assignment.group_assignment.due_date = now + timedelta(weeks=1)
    student_assignment.group_assignment.distribution_date = now - timedelta(
        weeks=1
    )
    student_assignment.group_assignment.save()

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=old_datetime,
    )
    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=new_datetime,
    )

    add_answers(
        student,
        questions[:n_correct_second],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )
    add_answers(
        student,
        questions[n_correct_second:n_correct_first],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_correct_first:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_second:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=False,
    )

    assert student_assignment.grade == n_correct_second + 0.5 * (
        n_correct_first - n_correct_second
    )


def test_grade__other_assignments__all_answered_correct_first_and_none_second(
    student_assignment,
):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)
    now = datetime.now(pytz.utc)
    old_datetime = now - timedelta(weeks=2)
    new_datetime = now + timedelta(weeks=2)
    student_assignment.group_assignment.due_date = now + timedelta(weeks=1)
    student_assignment.group_assignment.distribution_date = now - timedelta(
        weeks=1
    )
    student_assignment.group_assignment.save()

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=old_datetime,
    )
    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=new_datetime,
    )

    add_answers(
        student,
        questions[:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_second:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=False,
    )

    assert student_assignment.grade == float(n_first) / 2


def test_grade__other_assignments__none_answered_correct_first_and_all_second(
    student_assignment,
):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)
    now = datetime.now(pytz.utc)
    old_datetime = now - timedelta(weeks=2)
    new_datetime = now + timedelta(weeks=2)
    student_assignment.group_assignment.due_date = now + timedelta(weeks=1)
    student_assignment.group_assignment.distribution_date = now - timedelta(
        weeks=1
    )
    student_assignment.group_assignment.save()

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=old_datetime,
    )
    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=new_datetime,
    )

    add_answers(
        student,
        questions[:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=True,
    )
    add_answers(
        student,
        questions[n_second:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=False,
    )

    assert student_assignment.grade == float(n_second) / 2


def test_grade__other_assignments__none_answered_correct_first_and_second(
    student_assignment,
):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)
    now = datetime.now(pytz.utc)
    old_datetime = now - timedelta(weeks=2)
    new_datetime = now + timedelta(weeks=2)
    student_assignment.group_assignment.due_date = now + timedelta(weeks=1)
    student_assignment.group_assignment.distribution_date = now - timedelta(
        weeks=1
    )
    student_assignment.group_assignment.save()

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=old_datetime,
    )
    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=new_datetime,
    )

    add_answers(
        student,
        questions[:n_second],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
    )
    add_answers(
        student,
        questions[n_second:n_first],
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=False,
    )

    assert not student_assignment.grade


def test_grade__other_assignments__same_time__old_correct_new_incorrect(
    student_assignment,
):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)
    now = datetime.now(pytz.utc)
    old_datetime = now - timedelta(weeks=1)
    student_assignment.group_assignment.due_date = now + timedelta(weeks=1)
    student_assignment.group_assignment.distribution_date = now - timedelta(
        weeks=2
    )
    student_assignment.group_assignment.save()

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=old_datetime,
    )

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
    )

    assert student_assignment.grade == n


def test_grade__other_assignments__same_time__old_incorrect_new_correct(
    student_assignment,
):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)
    now = datetime.now(pytz.utc)
    old_datetime = now - timedelta(weeks=1)
    student_assignment.group_assignment.due_date = now + timedelta(weeks=1)
    student_assignment.group_assignment.distribution_date = now - timedelta(
        weeks=2
    )
    student_assignment.group_assignment.save()

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
        datetime_start=old_datetime,
    )

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )

    assert student_assignment.grade == n


def test_grade__other_assignments__same_time__both_correct(
    student_assignment,
):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)
    now = datetime.now(pytz.utc)
    old_datetime = now - timedelta(weeks=1)
    student_assignment.group_assignment.due_date = now + timedelta(weeks=1)
    student_assignment.group_assignment.distribution_date = now - timedelta(
        weeks=2
    )
    student_assignment.group_assignment.save()

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
        datetime_start=old_datetime,
    )

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=True,
        answer_second=True,
        correct_second=True,
    )

    assert student_assignment.grade == n


def test_grade__other_assignments__same_time__both_incorrect(
    student_assignment,
):
    assignment = student_assignment.group_assignment.assignment
    questions = assignment.questions.all()
    student = student_assignment.student
    n = len(questions)
    n_first = random.randint(1, n - 1)
    n_second = random.randint(1, n_first)
    now = datetime.now(pytz.utc)
    old_datetime = now - timedelta(weeks=1)
    student_assignment.group_assignment.due_date = now + timedelta(weeks=1)
    student_assignment.group_assignment.distribution_date = now - timedelta(
        weeks=2
    )
    student_assignment.group_assignment.save()

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
        datetime_start=old_datetime,
    )

    add_answers(
        student,
        questions,
        student_assignment.group_assignment.assignment,
        correct_first=False,
        answer_second=True,
        correct_second=False,
    )

    assert not student_assignment.grade
