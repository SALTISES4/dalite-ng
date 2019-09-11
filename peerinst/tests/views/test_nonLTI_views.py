from datetime import datetime

import pytz
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group, Permission, User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase, TransactionTestCase

from peerinst.models import (
    Assignment,
    Collection,
    Discipline,
    Question,
    Teacher,
)
from quality.models import UsesCriterion
from tos.models import Consent, Role, Tos


def ready_user(pk):
    user = User.objects.get(pk=pk)
    user.text_pwd = user.password
    user.password = make_password(user.text_pwd)
    user.save()
    return user


class LandingPageTest(TransactionTestCase):
    def setUp(self):
        physics = Discipline.objects.create(title="Physics")
        math = Discipline.objects.create(title="Math")
        chemistry = Discipline.objects.create(title="Chemistry")

        Question.objects.create(title="A", text="text", discipline=physics)
        Question.objects.create(title="B", text="text", discipline=physics)
        Question.objects.create(title="C", text="text", discipline=physics)

        Question.objects.create(title="D", text="text", discipline=math)
        Question.objects.create(title="E", text="text", discipline=math)

        Question.objects.create(title="F", text="text", discipline=chemistry)

    def test_discipline_stats(self):
        self.assertEqual(Question.objects.count(), 6)
        self.assertEqual(Discipline.objects.count(), 3)

        response = self.client.get(reverse("landing_page"))

        self.assertEqual(response.context["disciplines"][0]["name"], "All")
        self.assertEqual(response.context["disciplines"][1]["name"], "Physics")
        self.assertEqual(response.context["disciplines"][2]["name"], "Math")
        self.assertEqual(
            response.context["disciplines"][3]["name"], "Chemistry"
        )


class SignUpTest(TestCase):
    def test_which_template(self):
        response = self.client.get(reverse("sign_up"))
        self.assertTemplateUsed(response, "registration/sign_up.html")

    def test_invalid_form_post(self):
        response = self.client.post(reverse("sign_up"), data={})
        self.assertIn("This field is required", response.content.decode())

    def test_valid_form_post(self):
        response = self.client.post(
            reverse("sign_up"),
            data={
                "username": "abc",
                "password1": "jdefngath4",
                "password2": "jdefngath4",
                "email": "abc@def.com",
                "url": "http://abc.com",
            },
        )
        self.assertTemplateUsed(response, "registration/sign_up_done.html")
        self.assertTemplateUsed(
            response, "registration/sign_up_admin_email_html.html"
        )

    def test_email_error(self):

        with self.settings(EMAIL_BACKEND=""):
            response = self.client.post(
                reverse("sign_up"),
                data={
                    "username": "abc",
                    "password1": "jdefngath4",
                    "password2": "jdefngath4",
                    "email": "abc@def.com",
                    "url": "http://abc.com",
                },
                follow=True,
            )
        self.assertEqual(response.status_code, 503)
        self.assertTemplateUsed(response, "503.html")


class AdminTest(TestCase):
    fixtures = ["test_users.yaml"]

    def setUp(self):
        self.admin = ready_user(99)

    def test_dashboard(self):
        logged_in = self.client.login(
            username=self.admin.username, password=self.admin.text_pwd
        )
        self.assertTrue(logged_in)

        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "peerinst/dashboard.html")

        response = self.client.post(reverse("dashboard"), {"user": 3})
        self.assertTrue(User.objects.get(pk=3).is_active)
        self.assertRaises(
            Teacher.DoesNotExist, Teacher.objects.get, user__pk=3
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, "Please verify your myDalite account"
        )

        inactive_user = User.objects.get(pk=3)
        inactive_user.is_active = False
        inactive_user.save()

        with self.settings(EMAIL_BACKEND=""):
            response = self.client.post(
                reverse("dashboard"), {"user": 3, "is_teacher": "on"}
            )
            self.assertTrue(User.objects.get(pk=3).is_active)
            self.assertTrue(Teacher.objects.get(user__pk=3))
            self.assertEqual(response.status_code, 503)
            self.assertTemplateUsed(response, "503.html")


class TeacherTest(TestCase):
    fixtures = ["test_users.yaml"]

    def setUp(self):
        self.validated_teacher = ready_user(1)
        self.other_teacher = ready_user(2)
        self.inactive_user = ready_user(3)
        self.guest = ready_user(11)

        # Skip TOS interactions
        role = Role.objects.get(role="teacher")
        tos = Tos(version=1, text="Test", current=True, role=role)
        tos.save()
        consent = Consent(
            user=self.validated_teacher, accepted=True, tos=Tos.objects.first()
        )
        consent.save()

        self.group = Group.objects.get(name="Teacher")
        self.assertFalse(self.group.permissions.all())

        permission = Permission.objects.get(codename="add_question")
        self.group.permissions.add(permission)
        permission = Permission.objects.get(codename="change_question")
        self.group.permissions.add(permission)
        self.assertEqual(self.group.permissions.count(), 2)

        self.assertFalse(self.validated_teacher.get_all_permissions())

    def test_login_and_access_to_accounts(self):
        # Login
        response = self.client.post(
            reverse("login"),
            {
                "username": self.validated_teacher.username,
                "password": self.validated_teacher.text_pwd,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "peerinst/teacher/dashboard.html")

        # Test access to other
        response = self.client.get(reverse("teacher", kwargs={"pk": 2}))
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")

        # Test access to non-existent
        response = self.client.get(reverse("teacher", kwargs={"pk": 3}))
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

        # Logout
        response = self.client.get(reverse("logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

        # Attempt access after logout
        response = self.client.get(
            reverse("teacher", kwargs={"pk": 1}), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_refuse_inactive_at_login(self):
        # @login_required decorator and mixin do NOT check if user.is_active
        # but authentication backend should.
        #
        # Check inactive user cannot login
        logged_in = self.client.login(
            username=self.inactive_user.username,
            password=self.inactive_user.text_pwd,
        )
        self.assertFalse(logged_in)

    def test_adding_permissions(self):
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        response = self.client.get(reverse("question-create"))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse("welcome"))
        self.assertRedirects(response, reverse("teacher-dashboard"))
        self.assertIn(self.group, self.validated_teacher.groups.all())

        response = self.client.get(reverse("question-create"))
        self.assertEqual(response.status_code, 200)

    def test_redirect_logged_in_user(self):
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        response = self.client.get(reverse("login"), follow=True)
        self.assertTemplateNotUsed(response, "registration/login.html")

        self.client.logout()
        response = self.client.get(reverse("welcome"), follow=True)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_question_list_view(self):
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        # List matches assignment object
        response = self.client.get(
            reverse("question-list", kwargs={"assignment_id": "Assignment1"})
        )
        self.assertEqual(response.status_code, 200)
        self.assertItemsEqual(
            response.context["object_list"],
            Assignment.objects.get(pk="Assignment1").questions.all(),
        )

        # Assignment pk invalid -> 404
        response = self.client.get(
            reverse("question-list", kwargs={"assignment_id": "unknown_id"})
        )
        self.assertEqual(response.status_code, 404)

    def test_question_create(self):
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        # Step 1, without peerinst.add_question -> 403
        response = self.client.get(reverse("question-create"))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            reverse("question-create"),
            {
                "text": "Text of new question",
                "title": "New question",
                "answer_style": 0,
                "image": "",
                "video_url": "",
                "rationale_selection_algorithm": "prefer_expert_and_highly_voted",  # noqa
                "grading_scheme": 0,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 403)

        # Step 1, with peerinst.add_question & peerinst.change_question -> 200
        permission = Permission.objects.get(codename="add_question")
        self.validated_teacher.user_permissions.add(permission)
        permission = Permission.objects.get(codename="change_question")
        self.validated_teacher.user_permissions.add(permission)

        # NB: it is good practice to refresh from db after permissions change
        self.validated_teacher = User.objects.get(pk=1)

        self.assertTrue(
            self.validated_teacher.has_perm("peerinst.add_question")
        )
        self.assertTrue(
            self.validated_teacher.has_perm("peerinst.change_question")
        )

        question_count = Question.objects.count()

        response = self.client.get(reverse("question-create"))
        self.assertContains(response, "Step 1")

        response = self.client.post(
            reverse("question-create"),
            {
                "text": "Text of new question",
                "title": "New question",
                "type": "PI",
                "answer_style": 0,
                "category": 1,
                "image": "",
                "video_url": "",
                "rationale_selection_algorithm": "prefer_expert_and_highly_voted",  # noqa
                "grading_scheme": 0,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "peerinst/question/answer_choice_form.html"
        )
        self.assertEqual(Question.objects.count(), question_count + 1)

    def test_question_update(self):
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        # Step 1 (as edit) without ownership --> 403
        response = self.client.get(
            reverse("question-update", kwargs={"pk": 28})
        )
        self.assertEqual(response.status_code, 403)

        # Step 1 (as edit) with ownership and permission --> 200
        permission = Permission.objects.get(codename="change_question")
        self.validated_teacher.user_permissions.add(permission)
        response = self.client.get(
            reverse("question-update", kwargs={"pk": 32})
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("question-update", kwargs={"pk": 32}),
            {
                "text": "Text of new question",
                "title": "New question",
                "type": "PI",
                "answer_style": 0,
                "category": 1,
                "image": "",
                "video_url": "",
                "rationale_selection_algorithm": "prefer_expert_and_highly_voted",  # noqa
                "grading_scheme": 0,
                "collaborators": 2,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Question.objects.get(pk=32).collaborators.first(), 2)

        # Step 1 (as edit) as collaborator with permission --> 200
        response = self.client.get(
            reverse("question-update", kwargs={"pk": 33})
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("question-update", kwargs={"pk": 33}),
            {
                "text": "Text of new question",
                "title": "New title for question 5",
                "type": "PI",
                "answer_style": 0,
                "category": 1,
                "image": "",
                "video_url": "",
                "rationale_selection_algorithm": "prefer_expert_and_highly_voted",  # noqa
                "grading_scheme": 0,
                "collaborators": 2,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            self.other_teacher, Question.objects.get(pk=33).collaborators.all()
        )
        self.assertEqual(
            Question.objects.get(pk=33).title, "New title for question 5"
        )

        # Step 1, access if student answer exists -> Message
        q = Question.objects.get(pk=29)
        q.user = self.validated_teacher
        q.save()
        self.assertEqual(
            self.validated_teacher, Question.objects.get(pk=29).user
        )

        response = self.client.get(
            reverse("question-update", kwargs={"pk": 29})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Question properties cannot be changed if any students have "
            "submitted an answer",
        )
        self.assertNotContains(
            response,
            '<form id="question-create-form" enctype="multipart/form-data" '
            'method="post">',
        )

        response = self.client.post(
            reverse("question-update", kwargs={"pk": 29}),
            {
                "text": "Text of new question",
                "title": "New title for question",
                "answer_style": 0,
                "image": "",
                "video_url": "",
                "rationale_selection_algorithm": "prefer_expert_and_highly_voted",  # noqa
                "grading_scheme": 0,
                "collaborators": 2,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_answer_choice_create(self):
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        # db check
        self.assertEqual(Question.objects.count(), 6)

        # Step 2, without ownership -> 403
        response = self.client.get(
            reverse("answer-choice-form", kwargs={"question_id": 30})
        )
        self.assertEqual(response.status_code, 403)

        # Step 2, with ownership but no permission -> 403
        response = self.client.get(
            reverse("answer-choice-form", kwargs={"question_id": 32})
        )
        self.assertEqual(response.status_code, 403)

        # Step 2, with ownership and permission -> 200
        permission = Permission.objects.get(codename="change_question")
        self.validated_teacher.user_permissions.add(permission)
        response = self.client.get(
            reverse("answer-choice-form", kwargs={"question_id": 32})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["question"], Question.objects.get(pk=32)
        )
        self.assertContains(
            response, '<form id="answer-choice-form" method="post">'
        )

        # ... test post (to do but need to send formset in POST) -> 302 to step
        # 3
        # response = self.client.post(reverse('answer-choice-form', kwargs={
        # 'question_id' : 32 }), {'question' : 32, 'text' : 'Choice 1'},
        # follow=True)
        # self.assertEqual(response.status_code, 200)

        # Step 2, access if student answer exists -> Message
        q = Question.objects.get(pk=29)
        q.user = self.validated_teacher
        q.save()
        self.assertEqual(
            self.validated_teacher, Question.objects.get(pk=29).user
        )

        response = self.client.get(
            reverse("answer-choice-form", kwargs={"question_id": 29})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Answer choices cannot be changed if any students have answered "
            "this question",
        )
        self.assertNotContains(
            response, '<form id="answer-choice-form" method="post">'
        )

    def test_sample_answers(self):
        # Step 3, teacher
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        answer_count = (
            Question.objects.get(pk=29)
            .answer_set.filter(user_token__exact="")
            .count()
        )
        UsesCriterion.objects.filter(
            quality__quality_type__type="global"
        ).delete()
        response = self.client.post(
            reverse("sample-answer-form", kwargs={"question_id": 29}),
            {
                "first_answer_choice": 1,
                "rationale": "Test sample rationale 1",
                "datetime_start": datetime.now(pytz.utc).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                ),
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse("sample-answer-form", kwargs={"question_id": 29}),
            {
                "first_answer_choice": 2,
                "rationale": "Test sample rationale 2",
                "datetime_start": datetime.now(pytz.utc).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                ),
            },
            follow=True,
        )
        response = self.client.post(
            reverse("sample-answer-form", kwargs={"question_id": 29}),
            {
                "first_answer_choice": 3,
                "rationale": "Test sample rationale 3",
                "datetime_start": datetime.now(pytz.utc).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                ),
            },
            follow=True,
        )
        response = self.client.post(
            reverse("sample-answer-form", kwargs={"question_id": 29}),
            {
                "first_answer_choice": 4,
                "rationale": "Test sample rationale 4",
                "datetime_start": datetime.now(pytz.utc).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                ),
            },
            follow=True,
        )
        response = self.client.post(
            reverse("sample-answer-form", kwargs={"question_id": 29}),
            {
                "first_answer_choice": 5,
                "rationale": "Test sample rationale 5",
                "datetime_start": datetime.now(pytz.utc).strftime(
                    "%Y-%m-%d %H:%M:%S.%f"
                ),
            },
            follow=True,
        )
        self.assertEqual(
            answer_count + 5,
            Question.objects.get(pk=29)
            .answer_set.filter(user_token__exact="")
            .count(),
        )

        # Step 3, auto-add to an assignment for teacher
        # NB: Question doesn't have to belong to teacher but assignment does
        self.client.logout()
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        # Check that form is there if allowed
        response = self.client.get(
            reverse("sample-answer-form", kwargs={"question_id": 29})
        )
        self.assertContains(response, 'id="add_question_to_assignment"')

        assignment = Assignment.objects.get(pk="Assignment1")
        self.assertNotIn(
            Question.objects.get(pk=31), assignment.questions.all()
        )
        response = self.client.post(
            reverse("sample-answer-form-done", kwargs={"question_id": 31}),
            {"assignments": "Assignment1"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            Question.objects.get(pk=31), assignment.questions.all()
        )

        assignment = Assignment.objects.get(pk="Assignment4")
        self.assertNotIn(
            Question.objects.get(pk=31), assignment.questions.all()
        )
        response = self.client.post(
            reverse("sample-answer-form-done", kwargs={"question_id": 31}),
            {"assignments": "Assignment4"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(Question.objects.get(pk=31), assignment.questions.all())

        # Step 3, auto-add to an assignment for different teacher -> Invalid
        # form -> Teacher account page
        self.assertNotIn(
            Question.objects.get(pk=32), assignment.questions.all()
        )
        response = self.client.post(
            reverse("sample-answer-form-done", kwargs={"question_id": 32}),
            {"assignments": "Assignment3"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "peerinst/teacher/details.html")
        self.assertNotIn(
            Question.objects.get(pk=32), assignment.questions.all()
        )

        # Step 3, not a teacher as post -> 403 due to TOS mixin
        self.client.logout()
        logged_in = self.client.login(
            username=self.guest.username, password=self.guest.text_pwd
        )
        self.assertTrue(logged_in)

        response = self.client.post(
            reverse("sample-answer-form-done", kwargs={"question_id": 32}),
            {"assignments": "Assignment3"},
            follow=True,
        )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(
            Question.objects.get(pk=32), assignment.questions.all()
        )

        # Step 3, any get -> 400
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        response = self.client.get(
            reverse("sample-answer-form-done", kwargs={"question_id": 32}),
            follow=True,
        )
        self.assertEqual(response.status_code, 400)

    def test_question_cloning(self):
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)
        permission = Permission.objects.get(codename="add_question")
        self.validated_teacher.user_permissions.add(permission)
        permission = Permission.objects.get(codename="change_question")
        self.validated_teacher.user_permissions.add(permission)

        # Clone question 43 from another user
        question = Question.objects.get(pk=43)
        response = self.client.get(
            reverse("question-clone", kwargs={"pk": 43})
        )
        self.assertContains(response, "Step 1")
        self.assertContains(response, "Cloned from")
        self.assertContains(response, question.title)
        self.assertContains(response, question.user.username)

        response = self.client.post(
            reverse("question-clone", kwargs={"pk": 43}),
            {
                "text": "Text of cloned question",
                "title": "Title for cloned question",
                "type": "PI",
                "answer_style": 0,
                "category": 1,
                "image": "",
                "video_url": "",
                "rationale_selection_algorithm": "prefer_expert_and_highly_voted",  # noqa
                "grading_scheme": 0,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "peerinst/question/answer_choice_form.html"
        )
        self.assertEqual(question, Question.objects.get(pk=43))
        new_question = Question.objects.get(title="Title for cloned question")
        self.assertNotEqual(question.pk, new_question.pk)
        self.assertEqual(self.validated_teacher, new_question.user)
        self.assertEqual(question, new_question.parent)

        # Inherit parent answer choices for initial
        response = self.client.get(
            reverse(
                "answer-choice-form", kwargs={"question_id": new_question.pk}
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_assignment_update_dispatch(self):
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        # Access as teacher, non-owner -> 403
        response = self.client.get(
            reverse(
                "assignment-update", kwargs={"assignment_id": "Assignment2"}
            )
        )
        self.assertEqual(response.status_code, 403)

        # Access as teacher, owner, but with student answers -> 403
        response = self.client.get(
            reverse(
                "assignment-update", kwargs={"assignment_id": "Assignment1"}
            )
        )
        self.assertEqual(response.status_code, 403)

        # Access as teacher, owner, with no student answers -> 200
        response = self.client.get(
            reverse(
                "assignment-update", kwargs={"assignment_id": "Assignment4"}
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["teacher"], self.validated_teacher.teacher
        )
        self.assertTemplateUsed(response, "peerinst/assignment_detail.html")

    def test_assignment_update_post(self):
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        # As teacher, post valid form to add question -> 200
        response = self.client.post(
            reverse(
                "assignment-update", kwargs={"assignment_id": "Assignment4"}
            ),
            {"q": 31},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "peerinst/assignment_detail.html")
        self.assertIn(
            Question.objects.get(pk=31),
            Assignment.objects.get(pk="Assignment4").questions.all(),
        )

        # As teacher, post valid form to add question with student answers ->
        # 403
        response = self.client.post(
            reverse(
                "assignment-update", kwargs={"assignment_id": "Assignment1"}
            ),
            {"q": 31},
            follow=True,
        )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(
            Question.objects.get(pk=31),
            Assignment.objects.get(pk="Assignment1").questions.all(),
        )

        # As teacher, post valid form to remove question -> 200
        response = self.client.post(
            reverse(
                "assignment-update", kwargs={"assignment_id": "Assignment4"}
            ),
            {"q": 31},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "peerinst/assignment_detail.html")
        self.assertNotIn(
            Question.objects.get(pk=31),
            Assignment.objects.get(pk="Assignment4").questions.all(),
        )

        # As teacher, post invalid form to add question -> 400
        response = self.client.post(
            reverse(
                "assignment-update", kwargs={"assignment_id": "Assignment4"}
            ),
            {"q": 3111231},
            follow=True,
        )
        self.assertEqual(response.status_code, 400)

        # As non-logged in user, post valid form to add question -> Login
        self.client.logout()
        response = self.client.post(
            reverse(
                "assignment-update", kwargs={"assignment_id": "Assignment4"}
            ),
            {"q": 31},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertNotIn(
            Question.objects.get(pk=31),
            Assignment.objects.get(pk="Assignment4").questions.all(),
        )

    def test_TOS_mixin(self):
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        consent = Consent(
            user=self.validated_teacher,
            accepted=False,
            tos=Tos.objects.first(),
        )
        consent.save()

        permission = Permission.objects.get(codename="add_question")
        self.validated_teacher.user_permissions.add(permission)
        permission = Permission.objects.get(codename="change_question")
        self.validated_teacher.user_permissions.add(permission)

        # Question create
        response = self.client.get(reverse("question-create"), follow=True)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "tos/tos_required.html")

        # Question clone
        response = self.client.get(
            reverse("question-clone", kwargs={"pk": 43}), follow=True
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "tos/tos_required.html")

        # Question update
        response = self.client.get(
            reverse("question-update", kwargs={"pk": 32}), follow=True
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "tos/tos_required.html")

        # Answer choice create/update
        response = self.client.get(
            reverse("answer-choice-form", kwargs={"question_id": 32}),
            follow=True,
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "tos/tos_required.html")

        # Sample answer create
        response = self.client.get(
            reverse("sample-answer-form", kwargs={"question_id": 32}),
            follow=True,
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "tos/tos_required.html")

        # Sample answer submit
        response = self.client.get(
            reverse("sample-answer-form-done", kwargs={"question_id": 32}),
            follow=True,
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "tos/tos_required.html")

    def test_question_delete(self):
        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        # 'Delete', i.e. hide, question for teacher (ajax only)
        response = self.client.post(
            reverse("question-delete"),
            {"pk": 32},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        q = Question.objects.get(pk=32)
        self.assertIn(
            q, self.validated_teacher.teacher.deleted_questions.all()
        )

        # Check this question is not searchable
        # response =
        # self.client.get(reverse('question-search')+"?search_string=Question&type=assignment&id=Assignment1")
        # print(response.context['search_results'])
        # self.assertNotIn(q, response.context['search_results'])

    def test_collection_private(self):

        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        # Create a private collection with other owner -> 403
        q = Collection.objects.create(
            title="test_title",
            description="test_description",
            private=True,
            owner=self.other_teacher.teacher,
            discipline=Discipline.objects.create(title="Physics"),
        )

        # for not owner teacher, all collection's pages -> 403
        response = self.client.get(
            reverse("collection-update", args=str(q.pk))
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            reverse("collection-detail", args=str(q.pk))
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            reverse("collection-distribute", args=str(q.pk))
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            reverse("collection-delete", args=str(q.pk))
        )
        self.assertEqual(response.status_code, 403)

    def test_collection_public_not_owner(self):

        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        # Make collection public -> 200 for distribute and detail
        q = Collection.objects.create(
            title="test_title",
            description="test_description",
            private=False,
            owner=self.other_teacher.teacher,
            discipline=Discipline.objects.create(title="Physics"),
        )

        response = self.client.get(
            reverse("collection-update", args=str(q.pk))
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            reverse("collection-distribute", args=str(q.pk))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(
            reverse("collection-detail", args=str(q.pk))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(
            reverse("collection-delete", args=str(q.pk))
        )
        self.assertEqual(response.status_code, 403)

    def test_collection_public_owner(self):

        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        # Make teacher owner -> 200 for all
        q = Collection.objects.create(
            title="test_title",
            description="test_description",
            private=False,
            owner=self.validated_teacher.teacher,
            discipline=Discipline.objects.create(title="Physics"),
        )

        response = self.client.get(
            reverse("collection-update", args=str(q.pk))
        )
        self.assertEqual(response.status_code, 200)

        print(response)
        self.assertContains(
            response,
            '<form enctype="multipart/form-data" id="collection-update-form" method="post">',  # noqa
        )

        response = self.client.get(
            reverse("collection-delete", args=str(q.pk))
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, '<form id="collection-delete-form" method="post">'
        )

        # all list views should always return 200 for teacher
        # collection is in public domain and owned, so contained on those pages
        response = self.client.get(reverse("collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)
        self.assertContains(response, "Browse Collections")

        response = self.client.get(reverse("followed-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)
        self.assertContains(response, "Your Followed Collections")

        response = self.client.get(reverse("featured-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)
        self.assertContains(response, "Featured Collections")

        response = self.client.get(reverse("personal-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)
        self.assertContains(response, "Your Collections")

    def test_collection_public_owner_follower(self):

        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        q = Collection.objects.create(
            title="test_title",
            description="test_description",
            private=False,
            owner=self.validated_teacher.teacher,
            discipline=Discipline.objects.create(title="Physics"),
        )
        q.followers.add(self.validated_teacher.teacher)
        q.save()

        # teacher is follower, collection contained on followed-list view
        response = self.client.get(reverse("collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("followed-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("featured-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

        response = self.client.get(reverse("personal-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

    def test_collection_public_owner_follower_featured(self):

        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        q = Collection.objects.create(
            title="test_title",
            description="test_description",
            private=False,
            owner=self.validated_teacher.teacher,
            discipline=Discipline.objects.create(title="Physics"),
            featured=True,
        )
        q.followers.add(self.validated_teacher.teacher)
        q.save()

        # collection is featured, should appear on featured-list view
        response = self.client.get(reverse("collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("followed-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("featured-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("personal-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

    def test_collection_private_owner_follower_featured(self):

        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        q = Collection.objects.create(
            title="test_title",
            description="test_description",
            private=True,
            owner=self.validated_teacher.teacher,
            discipline=Discipline.objects.create(title="Physics"),
            featured=True,
        )
        q.followers.add(self.validated_teacher.teacher)
        q.save()

        # teacher = owner, so private attribute should not affect collection
        response = self.client.get(reverse("collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("followed-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("featured-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("personal-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

    def test_collection_private_owner_follower(self):

        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        q = Collection.objects.create(
            title="test_title",
            description="test_description",
            private=True,
            owner=self.validated_teacher.teacher,
            discipline=Discipline.objects.create(title="Physics"),
            featured=False,
        )
        q.followers.add(self.validated_teacher.teacher)
        q.save()

        # collection is removed from featured view
        response = self.client.get(reverse("collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("followed-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("featured-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

        response = self.client.get(reverse("personal-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

    def test_collection_private_owner(self):

        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        q = Collection.objects.create(
            title="test_title",
            description="test_description",
            private=True,
            owner=self.validated_teacher.teacher,
            discipline=Discipline.objects.create(title="Physics"),
            featured=False,
        )

        # collection is removed from teacher's followed collections
        response = self.client.get(reverse("collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("followed-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

        response = self.client.get(reverse("featured-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

        response = self.client.get(reverse("personal-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

    def test_collection_private(self):

        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        q = Collection.objects.create(
            title="test_title",
            description="test_description",
            private=True,
            owner=self.other_teacher.teacher,
            discipline=Discipline.objects.create(title="Physics"),
            featured=False,
        )

        # teacher loses ownership, collection should not appear on any list
        response = self.client.get(reverse("collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

        response = self.client.get(reverse("followed-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

        response = self.client.get(reverse("featured-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

        response = self.client.get(reverse("personal-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

    def test_collection_private_featured(self):

        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        q = Collection.objects.create(
            title="test_title",
            description="test_description",
            private=True,
            owner=self.other_teacher.teacher,
            discipline=Discipline.objects.create(title="Physics"),
            featured=True,
        )

        # featured collection is still private, not accesable
        response = self.client.get(reverse("collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

        response = self.client.get(reverse("followed-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

        response = self.client.get(reverse("featured-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

        response = self.client.get(reverse("personal-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

    def test_collection_private_featured_follower(self):

        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        q = Collection.objects.create(
            title="test_title",
            description="test_description",
            private=True,
            owner=self.other_teacher.teacher,
            discipline=Discipline.objects.create(title="Physics"),
            featured=True,
        )
        q.followers.add(self.validated_teacher.teacher)
        q.save()

        # followed collection is still private, not accesable
        response = self.client.get(reverse("collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

        response = self.client.get(reverse("followed-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

        response = self.client.get(reverse("featured-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

        response = self.client.get(reverse("personal-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)

    def test_collection_public_follower(self):

        logged_in = self.client.login(
            username=self.validated_teacher.username,
            password=self.validated_teacher.text_pwd,
        )
        self.assertTrue(logged_in)

        q = Collection.objects.create(
            title="test_title",
            description="test_description",
            private=False,
            owner=self.other_teacher.teacher,
            discipline=Discipline.objects.create(title="Physics"),
            featured=True,
        )
        q.followers.add(self.validated_teacher.teacher)
        q.save()

        # collection is now public, should appear on followed & featured lists
        response = self.client.get(reverse("collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("followed-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("featured-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, q.title)

        response = self.client.get(reverse("personal-collection-list"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, q.title)


class CustomMiddlewareTest(TestCase):
    def test_405_response(self):
        response = self.client.post(reverse("landing_page"), follow=True)
        # print(response)

        self.assertEqual(response.status_code, 405)
        self.assertTemplateUsed(response, "405.html")
