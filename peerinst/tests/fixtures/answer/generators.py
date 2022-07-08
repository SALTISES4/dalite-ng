import random
from datetime import datetime, timedelta, timezone

from peerinst.models import Answer, AnswerChoice, ShownRationale


def new_answer_choice(n, question):
    def generator():
        i = 0
        while True:
            i += 1
            yield {
                "question": question,
                "text": f"choice{i}",
                "correct": i == 1,
            }

    gen = generator()
    return [next(gen) for _ in range(n)]


def add_answer_choices(answer_choices):
    answer_choices = (
        [answer_choices]
        if isinstance(answer_choices, AnswerChoice)
        else answer_choices
    )
    return [AnswerChoice.objects.create(**a) for a in answer_choices]


def new_first_answers_no_shown(
    n, students, question, assignment, answer_choices
):
    def generator():
        i = 0
        while True:
            i += 1
            yield {
                "question": question,
                "assignment": assignment,
                "first_answer_choice": ((i - 1) % len(answer_choices)) + 1,
                "rationale": f"rationale{i}",
                "user_token": students[
                    (i - 1) // (len(answer_choices))
                ].student.username,
                "datetime_start": datetime.now(timezone.utc)
                + timedelta(minutes=i),
                "datetime_first": datetime.now(timezone.utc)
                + timedelta(minutes=1 + i),
                "datetime_second": datetime.now(timezone.utc)
                + timedelta(minutes=2 + i),
            }

    gen = generator()
    return [next(gen) for _ in range(n)]


def add_first_answers_no_shown(answers):
    answers = [answers] if isinstance(answers, Answer) else answers
    return [Answer.objects.create(**a) for a in answers]


def add_shown_and_second(first_answers_no_shown, n=0):
    choices = {a.first_answer_choice for a in first_answers_no_shown}
    for i, answer in enumerate(first_answers_no_shown):
        if not n and i >= n:
            break
        shown_self = [
            a
            for a in first_answers_no_shown
            if a.first_answer_choice == answer.first_answer_choice
        ]
        if len(shown_self) < 2:
            raise ValueError("You need at least 3 answers for each choice.")
        other_choice = random.choice(choices - {answer.first_answer_choice})
        shown_other = [
            a
            for a in first_answers_no_shown
            if a.first_answer_choice == other_choice.first_answer_choice
        ]
        if len(shown_other) < 2:
            raise ValueError("You need at least 3 answers for each choice.")
        shown = shown_self[:2] + shown_other[:2]
        for _answer in shown:
            ShownRationale.objects.create(
                shown_for_answer=answer, shown_answer=_answer
            )
        if random.random() > 0.5:
            answer.second_answer_choice = other_choice.first_answer_choice
            answer.chosen_rationale = random.choice(shown_other).rationale
        else:
            answer.second_answer_choice = answer.first_answer_choice
        answer.save()


def new_answers_rationale_only(
    n, student, question_rationale_only, assignment, answer_choice
):
    def generator():
        i = 0
        while True:
            i += 1
            yield {
                "question": question_rationale_only,
                "assignment": assignment,
                "first_answer_choice": 0,
                "rationale": f"rationale{i}",
                "user_token": student.student.username,
            }

    gen = generator()
    return [next(gen) for _ in range(n)]


def add_answers_rationale_only(answers):
    answers = [answers] if isinstance(answers, Answer) else answers
    return [Answer.objects.create(**a) for a in answers]
