from __future__ import unicode_literals

import pytest

from peerinst.tests.fixtures import *  # noqa
from peerinst.util import report_data_by_assignment

from .fixtures import *  # noqa F403


@pytest.mark.django_db
def test_report_data_by_assignment_no_answers(assignments, groups, teacher):
    full_report = report_data_by_assignment(
        assignments, [g.pk for g in groups], teacher
    )

    for assignment, report in zip(assignments, full_report):

        assert report["assignment"] == assignment.title
        assert report["transitions"] == []
        assert len(report["questions"]) == len(assignment.questions.all())

        for question in assignment.questions.all():
            question_ = next(
                q for q in report["questions"] if q["title"] == question.title
            )
            answer_choices = question.answerchoice_set.all()

            assert all(
                q == qq
                for q, qq in zip(question_["answer_choices"], answer_choices)
            )
            assert question_["question_image"] == question.image
            assert question_["title"] == question.title
            assert question_["text"] == question.text
            assert question_["student_responses"] == []
            assert question_["num_responses"] == 0

            assert question_["transitions"] == [
                {"data": [], "label": "Transition"}
            ]

            assert len(question_["confusion_matrix"]) == len(answer_choices)

            for i, choice in enumerate(answer_choices):
                choice_ = next(
                    c
                    for c in question_["confusion_matrix"]
                    if c["first_answer_choice"] == i + 1
                )
                assert choice_["first_answer_choice"] == i + 1
                for j, second in enumerate(choice_["second_answer_choice"]):
                    assert second["value"] == j + 1
                    assert second["N"] == 0

            labels = ["First Answer Choice", "Second Answer Choice"]

            for label, choice in zip(
                labels, question_["answer_distributions"]
            ):
                assert choice["label"] == label
                assert choice["data"] == []
