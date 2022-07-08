from itertools import repeat
from unittest import mock

import ddt
from django.test import TestCase
from django.urls import reverse

from .. import admin, admin_views, models
from . import factories


class AggregatesTestCase(TestCase):
    fixtures = ["peerinst_test_data"]

    def test_get_question_aggregates(self):
        assignment = models.Assignment.objects.get(identifier="Assignment1")

        question = models.Question.objects.get(id=29)
        sums, students = admin_views.get_question_aggregates(
            assignment, question
        )
        expected_sums = {
            "correct_first_answers": 6,
            "correct_second_answers": 3,
            "switches": 9,
            ("switches", 1): 2,
            ("switches", 2): 1,
            ("switches", 3): 3,
            ("switches", 4): 3,
            "total_answers": 14,
        }
        self.assertDictEqual(dict(sums), expected_sums)
        expected_students = {
            "bmnwf",
            "eeawg",
            "esbxa",
            "kmhti",
            "nrqek",
            "qsrzd",
            "rhtof",
            "upjwt",
            "yosbj",
        }
        self.assertSetEqual(students, expected_students)

        question = models.Question.objects.get(id=30)
        sums, students = admin_views.get_question_aggregates(
            assignment, question
        )
        expected_sums = {
            "correct_first_answers": 3,
            "correct_second_answers": 3,
            "switches": 6,
            ("switches", 1): 3,
            ("switches", 2): 3,
            "total_answers": 6,
        }
        self.assertDictEqual(dict(sums), expected_sums)
        expected_students = {
            "askvw",
            "ciuaq",
            "etgfe",
            "glepb",
            "kmhti",
            "nrqek",
        }
        self.assertSetEqual(students, expected_students)

    def test_get_assignment_aggregates(self):
        assignment = models.Assignment.objects.get(identifier="Assignment1")

        sums, unused_question_data = admin_views.get_assignment_aggregates(
            assignment
        )
        expected_sums = {
            "correct_first_answers": 9,
            "correct_second_answers": 6,
            "switches": 15,
            ("switches", 1): 5,
            ("switches", 2): 4,
            ("switches", 3): 3,
            ("switches", 4): 3,
            "total_answers": 20,
            "total_students": 13,
        }
        self.assertDictEqual(dict(sums), expected_sums)


class TopRationalesTestData:
    @staticmethod
    def getData(count):
        assignment = factories.AssignmentFactory()
        question = factories.QuestionFactory(
            choices=2,
            choices__correct=[1],
        )
        assignment.questions.add(question)

        # Many chosen rationales, with long text
        answers = []
        for idx in range(count):
            first_answer = (idx % 2) + 1  # 1, 2, 1, 2, ...
            second_answer = 1 if (idx % 4) < 2 else 2  # 1, 1, 2, 2, ...
            upvotes = idx % 10
            chosen_rationale = answers[idx - 1] if idx else None
            rationale = "Rationale " + str(idx) * 200
            answers += [
                factories.AnswerFactory(
                    assignment=assignment,
                    question=question,
                    first_answer_choice=first_answer,
                    second_answer_choice=second_answer,
                    user_token="etfge",
                    upvotes=upvotes,
                    chosen_rationale=chosen_rationale,
                    rationale=rationale,
                ),
            ]
        return (assignment, question)

    @staticmethod
    def mock_rationale_aggregates(
        question, assignment, perpage, *args, **kwargs
    ):
        sums = {
            "upvoted": 1,
            "chosen": 150,
            "right_to_wrong": 12,
            "wrong_to_right": 50,
        }
        answer = mock.Mock()

        if (
            (perpage is None)
            or (perpage <= 0)
            or (perpage > admin.AnswerAdmin.list_per_page)
        ):
            perpage = admin.AnswerAdmin.list_per_page

        rationales = {
            "upvoted": list(repeat(answer, min(perpage, 1))),
            "chosen": list(repeat(answer, min(perpage, 150))),
            "right_to_wrong": list(repeat(answer, min(perpage, 12))),
            "wrong_to_right": list(repeat(answer, min(perpage, 50))),
        }
        return sums, rationales


@ddt.ddt
class TopRationalesTestCase(TestCase):
    assignment = None
    question = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.assignment, cls.question) = TopRationalesTestData.getData(5000)

    @ddt.data(0, 100, 2, 1500)
    def test_large_data(self, perpage):
        with self.assertNumQueries(6 if perpage else 5):
            sums, rationales = admin_views.get_question_rationale_aggregates(
                self.assignment, self.question, perpage
            )
        self.assertEqual(sums["upvoted"], 4500)
        self.assertEqual(
            len(rationales["upvoted"]), perpage if perpage < 4500 else 4500
        )

        self.assertEqual(sums["chosen"], 5000)
        self.assertEqual(
            len(rationales["chosen"]), perpage if perpage < 5000 else 5000
        )

        self.assertEqual(sums["wrong_to_right"], 1250)
        self.assertEqual(
            len(rationales["wrong_to_right"]),
            perpage if perpage < 1250 else 1250,
        )
        self.assertEqual(sums["right_to_wrong"], 1250)
        self.assertEqual(
            len(rationales["right_to_wrong"]),
            perpage if perpage < 1250 else 1250,
        )

    @ddt.data(0, 100, 2)
    @mock.patch(
        "peerinst.admin_views.get_question_rationale_aggregates",
        TopRationalesTestData.mock_rationale_aggregates,
    )
    def test_view(self, perpage):

        admin_user = factories.UserFactory()
        admin_user.is_staff = True
        admin_user.save()

        self.client.login(username=admin_user.username, password="test")
        kwargs = dict(
            assignment_id=self.assignment.identifier,
            question_id=self.question.id,
        )
        url = reverse("question-rationales", kwargs=kwargs)
        if perpage:
            url = "?".join([url, f"perpage={perpage}"])
        else:
            perpage = admin.AnswerAdmin.list_per_page

        response = self.client.get(url)
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(context["perpage"], perpage)

        summary_data = context["summary_data"]
        self.assertEqual(len(summary_data), 4)
        self.assertEqual(summary_data[0], ("Total rationales upvoted", 1))
        self.assertEqual(summary_data[1], ("Total rationales chosen", 150))
        self.assertEqual(
            summary_data[2],
            ("Total rationales chosen for right to wrong answer switches", 12),
        )
        self.assertEqual(
            summary_data[3],
            ("Total rationales chosen for wrong to right answer switches", 50),
        )

        rationale_data = context["rationale_data"]
        self.assertEqual(len(rationale_data), 4)
        for data in rationale_data:
            self.assertListEqual(
                data["labels"],
                [
                    "Count",
                    "Rationale",
                    "Upvotes",
                    "Downvotes",
                    "Answers with this chosen rationale",
                ],
            )

        self.assertEqual(rationale_data[0]["heading"], "Upvoted rationales")
        self.assertEqual(len(rationale_data[0]["rows"]), 1)

        self.assertEqual(rationale_data[1]["heading"], "Top rationales chosen")
        self.assertEqual(
            len(rationale_data[1]["rows"]), perpage if perpage < 150 else 150
        )

        self.assertEqual(
            rationale_data[2]["heading"],
            "Top rationales chosen for right to wrong answer switches",
        )
        self.assertEqual(
            len(rationale_data[2]["rows"]), perpage if perpage < 12 else 12
        )

        self.assertEqual(
            rationale_data[3]["heading"],
            "Top rationales chosen for wrong to right answer switches",
        )
        self.assertEqual(
            len(rationale_data[3]["rows"]), perpage if perpage < 50 else 50
        )
