from datetime import datetime

import pytz

from peerinst.models import Answer, AnswerChoice


def add_answers(
    student,
    questions,
    assignment,
    correct_first=True,
    answer_second=True,
    correct_second=True,
    datetime_start=None,
    datetime_first=None,
    datetime_second=None,
):
    if not hasattr(questions, "__iter__"):
        questions = [questions]

    for question in questions:
        for i in range(2):
            AnswerChoice.objects.create(
                question=question,
                text="choice{}".format(i + 1),
                correct=i == 0,
            )

        Answer.objects.create(
            question=question,
            assignment=assignment,
            user_token=student.student.username,
            first_answer_choice=2 - correct_first,
            second_answer_choice=2 - correct_second if answer_second else None,
            datetime_start=datetime.now(pytz.utc)
            if datetime_start is None
            else datetime_start,
            datetime_first=datetime.now(pytz.utc)
            if datetime_first is None
            else datetime_first,
            datetime_second=datetime.now(pytz.utc)
            if datetime_second is None
            else datetime_second,
        )
