import json
import random
from datetime import datetime
from unittest import mock

import ddt
import pytest
import pytz
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from peerinst.forms import SignUpForm
from peerinst.models import (
    Answer,
    LtiEvent,
    NewUserRequest,
    Question,
    ShownRationale,
    Student,
    UserUrl,
)
from peerinst.tests import factories
from peerinst.util import SessionStageData
from quality.models import UsesCriterion


class Grade:
    CORRECT = 1.0
    INCORRECT = 0.0
    PARTIAL = 0.5


class QuestionViewTestCase(TestCase):

    ORG = "LTIX"
    COURSE_ID = f"course-v1:{ORG}+LTI-101+now"
    USAGE_ID = "block-v1:LTIX+LTI-101+now+type@lti+block@d41d8cd98f00b204e9800998ecf8427e"  # noqa
    LTI_PARAMS = {
        "context_id": COURSE_ID,
        "lis_outcome_service_url": (
            "https://courses.edx.org/courses/{course_id}/xblock/{usage_id}"
            "/handler_noauth/grade_handler"
        ).format(course_id=COURSE_ID, usage_id=USAGE_ID),
        "lis_result_sourcedid": "lis_result_sourcedid",
        "lti_version": "LTI-1p0",
        "resource_link_id": "resource_link_id",
        "user_id": "1234567890",
    }
    EXPECTED_RESULT_COLUMNS = [
        {"name": "label", "label": "Choice"},
        {"name": "before", "label": "Before"},
        {"name": "after", "label": "After"},
        {"name": "to_A", "label": "To A"},
        {"name": "to_B", "label": "To B"},
        {"name": "to_C", "label": "To C"},
        {"name": "to_D", "label": "To D"},
        {"name": "to_E", "label": "To E"},
    ]

    def setUp(self):
        super().setUp()

        UsesCriterion.objects.filter(
            quality__quality_type__type="global"
        ).delete()

        # TOS integration
        from tos.models import Consent, Role, Tos

        role = Role.objects.get(role="student")

        tos = Tos(version=1, text="Test", current=True, role=role)
        tos.save()
        no_share_user = User(username="no_share", email="test@test.com")
        no_share_user.save()
        # To test latest consent is used
        consent = Consent(
            user=no_share_user, accepted=True, tos=Tos.objects.first()
        )
        consent.save()
        no_consent = Consent(
            user=no_share_user, accepted=False, tos=Tos.objects.first()
        )
        no_consent.save()

        self.user = factories.UserFactory()
        s, _ = Student.objects.get_or_create(student=self.user)
        self.assignment = factories.AssignmentFactory()
        self.set_question(
            factories.QuestionFactory(
                choices=5, choices__correct=[2, 4], choices__rationales=4
            )
        )
        self.add_user_to_even_answers()
        self.addCleanup(mock.patch.stopall)

        grade_patcher = mock.patch(
            "peerinst.models.Answer.grade", new_callable=mock.PropertyMock
        )
        self.mock_grade = grade_patcher.start()
        self.mock_grade.return_value = Grade.CORRECT

    def add_user_to_even_answers(self):
        c = 0
        for a in self.question.answer_set.all():
            if c % 2 == 0:
                a.user_token = User.objects.get(username="no_share").username
                a.save()
            c = c + 1

    def set_question(self, question):
        self.question = question
        self.assignment.questions.add(question)
        self.answer_choices = question.get_choices()
        self.question_url = reverse(
            "question",
            kwargs=dict(
                assignment_id=self.assignment.pk, question_id=question.pk
            ),
        )
        self.custom_key = str(self.assignment.pk) + ":" + str(question.pk)
        self.log_in_with_lti()

    def log_in_with_scoring_disabled(self):
        """
        Log a user in pretending that scoring is disabled in the LMS.

        This is done by calling `log_in_with_lti` with a modified version of
        `LTI_PARAMS` that does not include `lis_outcome_service_url`.

        `lis_outcome_service_url` is the URL of the handler to use for sending
        grades to the LMS.
        It is only included in the LTI request if grading is enabled on the LMS
        side (otherwise there is no need to send back a grade).
        """
        lti_params = self.LTI_PARAMS.copy()
        del lti_params["lis_outcome_service_url"]
        self.log_in_with_lti(lti_params=lti_params)

    def get_results_view(self):
        response = self.client.get(
            self.question_url + "?show_results_view=true"
        )
        self.assertEqual(response.status_code, 200)
        return response

    def log_in_with_lti(self, user=None, password=None, lti_params=None):
        """Log a user in with fake LTI data."""
        if user is None:
            user = self.user
        if lti_params is None:
            lti_params = self.LTI_PARAMS.copy()
        lti_params["lis_person_sourcedid"] = user.username
        lti_params["lis_person_contact_email_primary"] = user.email
        lti_params["custom_assignment_id"] = str(self.assignment.pk)
        lti_params["custom_question_id"] = str(self.question.pk)

        self.client.login(username=user.username, password=password or "test")

    def question_get(self):
        # follow=True required in case of redirects
        response = self.client.get(self.question_url, follow=True)
        # commented out by Sam because on TOS integration is meant to redirect
        # (code 301) for new users
        # self.assertEqual(response.status_code, 200)
        return response

    def question_post(self, **form_data):
        form_data["datetime_start"] = datetime.now(pytz.utc).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )
        print(form_data)
        form_data = {k: v for k, v in form_data.items() if v is not None}
        response = self.client.post(self.question_url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        return response


class QuestionViewTest(QuestionViewTestCase):
    def run_standard_review_mode_extra_rationales(self):
        response = self.question_get()
        self.assertTemplateUsed(response, "peerinst/question/start.html")
        self.assertEqual(response.context["assignment"], self.assignment)
        self.assertEqual(response.context["question"], self.question)
        self.assertEqual(
            response.context["answer_choices"], self.answer_choices
        )

        # Provide a first answer and a rationale.
        first_answer_choice = 2
        first_choice_label = self.question.get_choice_label(2)
        rationale = "my rationale text"
        response = self.question_post(
            first_answer_choice=first_answer_choice, rationale=rationale
        )
        self.assertTemplateUsed(response, "peerinst/question/review.html")
        self.assertEqual(response.context["assignment"], self.assignment)
        self.assertEqual(response.context["question"], self.question)
        self.assertEqual(
            response.context["answer_choices"], self.answer_choices
        )
        self.assertEqual(
            response.context["first_choice_label"], first_choice_label
        )
        self.assertEqual(response.context["rationale"], rationale)
        self.assertEqual(response.context["sequential_review"], False)
        stage_data = SessionStageData(self.client.session, self.custom_key)
        rationale_choices = stage_data.get("rationale_choices")

        second_answer_choices = [
            choice
            for choice, unused_label, unused_rationales in rationale_choices
        ]
        self.assertIn(first_answer_choice, second_answer_choices)

        for a in self.question.answer_set.filter(user_token="no_share"):
            self.assertNotIn(a.rationale, str(rationale_choices))

        # Select a different answer during review.
        second_answer_choice = next(
            choice
            for choice in second_answer_choices
            if choice != first_answer_choice
        )
        second_choice_label = self.question.get_choice_label(
            second_answer_choice
        )
        chosen_rationale = int(rationale_choices[1][2][0][0])
        response = self.question_post(
            second_answer_choice=second_answer_choice,
            rationale_choice_1=chosen_rationale,
        )
        self.assertTemplateUsed(response, "peerinst/question/summary.html")
        self.assertEqual(response.context["assignment"], self.assignment)
        self.assertEqual(response.context["question"], self.question)
        self.assertEqual(
            response.context["answer_choices"], self.answer_choices
        )
        self.assertEqual(
            response.context["first_choice_label"], first_choice_label
        )
        self.assertEqual(
            response.context["second_choice_label"], second_choice_label
        )
        self.assertEqual(response.context["rationale"], rationale)
        self.assertEqual(
            response.context["chosen_rationale"].id, chosen_rationale
        )

        answer = Answer.objects.get(
            question=self.question,
            assignment=self.assignment,
            first_answer_choice=first_answer_choice,
            rationale=rationale,
        )
        shown_rationales = [
            Answer.objects.get(id=_rationale[0]) if _rationale[0] else None
            for _, _, rationales in rationale_choices
            for _rationale in rationales[:2]
        ]

        for _rationale in shown_rationales:
            try:
                ShownRationale.objects.get(
                    shown_for_answer=answer, shown_answer=_rationale
                )
            except ShownRationale.DoesNotExist:
                assert False

        unshown_rationales = [
            Answer.objects.get(id=_rationale[0]) if _rationale[0] else None
            for _, _, rationales in rationale_choices
            for _rationale in rationales[2:]
        ]

        for _rationale in unshown_rationales:
            self.assertFalse(
                ShownRationale.objects.filter(
                    shown_for_answer=answer, shown_answer=_rationale
                ).exists()
            )

        response = self.get_results_view()
        self.assertTemplateUsed(
            response, "peerinst/question/answers_summary.html"
        )
        self.assertEqual(response.context["question"], self.question)
        first_choice_row = next(
            row
            for row in response.context["answer_rows"]
            if first_choice_label in row[0]
        )
        second_choice_row = next(
            row
            for row in response.context["answer_rows"]
            if second_choice_label in row[0]
        )
        self.assertEqual(first_choice_row[1], 1)
        self.assertEqual(first_choice_row[2], 0)
        self.assertEqual(second_choice_row[1], 0)

    def run_standard_review_mode(self):
        """Test answering questions in default mode."""

        # Show the question and the form for the first answer and rationale.
        response = self.question_get()
        self.assertTemplateUsed(response, "peerinst/question/start.html")
        self.assertEqual(response.context["assignment"], self.assignment)
        self.assertEqual(response.context["question"], self.question)
        self.assertEqual(
            response.context["answer_choices"], self.answer_choices
        )

        # Provide a first answer and a rationale.
        first_answer_choice = 2
        first_choice_label = self.question.get_choice_label(2)
        rationale = "my rationale text"
        response = self.question_post(
            first_answer_choice=first_answer_choice, rationale=rationale
        )
        self.assertTemplateUsed(response, "peerinst/question/review.html")
        self.assertEqual(response.context["assignment"], self.assignment)
        self.assertEqual(response.context["question"], self.question)
        self.assertEqual(
            response.context["answer_choices"], self.answer_choices
        )
        self.assertEqual(
            response.context["first_choice_label"], first_choice_label
        )
        self.assertEqual(response.context["rationale"], rationale)
        self.assertEqual(response.context["sequential_review"], False)
        stage_data = SessionStageData(self.client.session, self.custom_key)
        rationale_choices = stage_data.get("rationale_choices")
        second_answer_choices = [
            choice
            for choice, unused_label, unused_rationales in rationale_choices
        ]
        self.assertIn(first_answer_choice, second_answer_choices)

        for a in self.question.answer_set.filter(user_token="no_share"):
            self.assertNotIn(a.rationale, str(rationale_choices))

        # Select a different answer during review.
        second_answer_choice = next(
            choice
            for choice in second_answer_choices
            if choice != first_answer_choice
        )
        second_choice_label = self.question.get_choice_label(
            second_answer_choice
        )
        chosen_rationale = int(rationale_choices[1][2][0][0])
        response = self.question_post(
            second_answer_choice=second_answer_choice,
            rationale_choice_1=chosen_rationale,
        )
        self.assertTemplateUsed(response, "peerinst/question/summary.html")
        self.assertEqual(response.context["assignment"], self.assignment)
        self.assertEqual(response.context["question"], self.question)
        self.assertEqual(
            response.context["answer_choices"], self.answer_choices
        )
        self.assertEqual(
            response.context["first_choice_label"], first_choice_label
        )
        self.assertEqual(
            response.context["second_choice_label"], second_choice_label
        )
        self.assertEqual(response.context["rationale"], rationale)
        self.assertEqual(
            response.context["chosen_rationale"].id, chosen_rationale
        )

        answer = Answer.objects.get(
            question=self.question,
            assignment=self.assignment,
            first_answer_choice=first_answer_choice,
            rationale=rationale,
        )
        shown_rationales = [
            Answer.objects.get(id=_rationale[0]) if _rationale[0] else None
            for _, _, rationales in rationale_choices
            for _rationale in rationales[:2]
        ]
        for _rationale in shown_rationales:
            try:
                ShownRationale.objects.get(
                    shown_for_answer=answer, shown_answer=_rationale
                )
            except ShownRationale.DoesNotExist:
                assert False

        response = self.get_results_view()
        self.assertTemplateUsed(
            response, "peerinst/question/answers_summary.html"
        )
        self.assertEqual(response.context["question"], self.question)
        first_choice_row = next(
            row
            for row in response.context["answer_rows"]
            if first_choice_label in row[0]
        )
        second_choice_row = next(
            row
            for row in response.context["answer_rows"]
            if second_choice_label in row[0]
        )
        self.assertEqual(first_choice_row[1], 1)
        self.assertEqual(first_choice_row[2], 0)
        self.assertEqual(second_choice_row[1], 0)

    def test_standard_review_mode(self):
        """Test answering questions in default mode, with scoring enabled."""
        self.mock_grade.return_value = Grade.INCORRECT
        self.run_standard_review_mode()
        self.assertTrue(self.mock_grade.called)

    def test_standard_review_mode_extra_rationales(self):
        """Test answering questions in default mode with extra rationales,
        with scoring enabled. Also testing shown rationales with no see more
        press."""
        self.set_question(
            factories.QuestionFactory(
                answer_style=Question.NUMERIC,
                choices=5,
                choices__correct=[2, 4],
                choices__rationales=6,
            )
        )
        self.mock_grade.return_value = Grade.INCORRECT
        self.run_standard_review_mode_extra_rationales()
        self.assertTrue(self.mock_grade.called)

    def test_numeric_answer_labels(self):
        """Test answering questions in default mode, using numerical labels."""
        self.set_question(
            factories.QuestionFactory(
                answer_style=Question.NUMERIC,
                choices=5,
                choices__correct=[2, 4],
                choices__rationales=4,
            )
        )
        self.EXPECTED_RESULT_COLUMNS = [
            {"name": "label", "label": "Choice"},
            {"name": "before", "label": "Before"},
            {"name": "after", "label": "After"},
            {"name": "to_1", "label": "To 1"},
            {"name": "to_2", "label": "To 2"},
            {"name": "to_3", "label": "To 3"},
            {"name": "to_4", "label": "To 4"},
            {"name": "to_5", "label": "To 5"},
        ]
        self.run_standard_review_mode()

    def test_standard_review_mode_scoring_disabled(self):
        """Test answering questions in default mode, with scoring disabled."""
        self.log_in_with_scoring_disabled()
        self.run_standard_review_mode()
        self.assertTrue(
            self.mock_grade.called
        )  # "emit_check_events" still uses "grade" to obtain grade data

    def test_sequential_review_mode(self):
        """Test answering questions in sequential review mode."""

        self.mock_grade.return_value = Grade.INCORRECT

        self.set_question(
            factories.QuestionFactory(
                sequential_review=True,
                choices=5,
                choices__correct=[2, 4],
                choices__rationales=4,
            )
        )

        # Show the question and the form for the first answer and rationale.
        response = self.question_get()
        self.assertTemplateUsed(response, "peerinst/question/start.html")
        self.assertEqual(response.context["assignment"], self.assignment)
        self.assertEqual(response.context["question"], self.question)
        self.assertEqual(
            response.context["answer_choices"], self.answer_choices
        )

        # Provide a first answer and a rationale.
        first_answer_choice = 2
        first_choice_label = self.question.get_choice_label(2)
        rationale = "my rationale text"
        response = self.question_post(
            first_answer_choice=first_answer_choice, rationale=rationale
        )

        # Loop over all rationales and vote on them.
        votes = []
        while "peerinst/question/sequential_review.html" in (
            template.name for template in response.templates
        ):
            self.assertTrue(response.context["current_rationale"])
            vote = random.choice(["upvote", "downvote"])
            votes.append(vote)
            response = self.question_post(**{vote: 1})

        # We've reached the final review.
        self.assertTemplateUsed(response, "peerinst/question/review.html")
        self.assertEqual(response.context["assignment"], self.assignment)
        self.assertEqual(response.context["question"], self.question)
        self.assertEqual(
            response.context["answer_choices"], self.answer_choices
        )
        self.assertEqual(
            response.context["first_choice_label"], first_choice_label
        )
        self.assertEqual(response.context["rationale"], rationale)
        self.assertEqual(response.context["sequential_review"], True)
        stage_data = SessionStageData(self.client.session, self.custom_key)
        rationale_choices = stage_data.get("rationale_choices")
        second_answer_choices = [
            choice
            for choice, unused_label, unused_rationales in rationale_choices
        ]
        self.assertIn(first_answer_choice, second_answer_choices)

        # Select a different answer during review.
        second_answer_choice = next(
            choice
            for choice in second_answer_choices
            if choice != first_answer_choice
        )
        second_choice_label = self.question.get_choice_label(
            second_answer_choice
        )
        chosen_rationale = int(rationale_choices[1][2][0][0])
        response = self.question_post(
            second_answer_choice=second_answer_choice,
            rationale_choice_1=chosen_rationale,
        )
        self.assertTemplateUsed(response, "peerinst/question/summary.html")
        self.assertEqual(response.context["assignment"], self.assignment)
        self.assertEqual(response.context["question"], self.question)
        self.assertEqual(
            response.context["answer_choices"], self.answer_choices
        )
        self.assertEqual(
            response.context["first_choice_label"], first_choice_label
        )
        self.assertEqual(
            response.context["second_choice_label"], second_choice_label
        )
        self.assertEqual(response.context["rationale"], rationale)
        self.assertEqual(
            response.context["chosen_rationale"].id, chosen_rationale
        )

        answer = Answer.objects.get(
            question=self.question,
            assignment=self.assignment,
            first_answer_choice=first_answer_choice,
            rationale=rationale,
        )
        shown_rationales = [
            Answer.objects.get(id=_rationale[0]) if _rationale[0] else None
            for _, _, rationales in rationale_choices
            for _rationale in rationales[:2]
        ]
        for _rationale in shown_rationales:
            try:
                ShownRationale.objects.get(
                    shown_for_answer=answer, shown_answer=_rationale
                )
            except ShownRationale.DoesNotExist:
                assert False

        self.assertTrue(self.mock_grade.called)


def test_signup__get(client):
    resp = client.get(reverse("sign_up"))
    assert "registration/sign_up.html" in [t.name for t in resp.templates]
    assert isinstance(resp.context["form"], SignUpForm)


def test_signup__post(client, mocker):
    data = {"username": "test", "email": "test@test.com", "url": "test.com"}
    mail_managers = mocker.patch("peerinst.views.views.mail_managers_async")
    resp = client.post(reverse("sign_up"), data)
    assert "registration/sign_up_done.html" in [t.name for t in resp.templates]
    assert User.objects.filter(
        username=data["username"], email=data["email"]
    ).exists()
    assert (
        UserUrl.objects.get(user__username=data["username"]).url
        == f"http://{data['url']}"
    )
    assert NewUserRequest.objects.filter(
        user__username=data["username"]
    ).exists()
    mail_managers.assert_called_once()


@pytest.mark.skip
def test_signup__backend_missing(client, mocker):
    data = {"username": "test", "email": "test@test.com", "url": "test.com"}
    settings = mocker.patch("peerinst.views.views.settings")
    settings.EMAIL_BACKEND = ""
    mail_managers = mocker.patch("peerinst.views.views.mail_managers_async")
    resp = client.post(reverse("sign_up"), data)
    assert resp.status_code == 503
