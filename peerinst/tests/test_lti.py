from unittest import mock
from urllib.parse import parse_qs, urlencode, urlparse

import oauthlib.oauth1
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.db import IntegrityError
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from lti_provider.tests.factories import BASE_LTI_PARAMS, generate_lti_request
from lti_provider.views import LTIRoutingView
from pylti.common import LTIException

from dalite.views import admin_index_wrapper
from peerinst.models import (
    Assignment,
    Question,
    Student,
    StudentGroup,
    Teacher,
)
from tos.models import Consent, Role, Tos


def generate_lti_request_dalite(
    client_key,
    teacher_id=None,
    assignment_id=None,
    question_id=None,
    user_credentials=None,
    **extra_params,
):
    """
    This code generated valid LTI 1.0 basic-lti-launch-request request
    It is a modified version of lti_provider.tests.factories.generate_lti_request
    but uses PYLTI_CONFIG with consumer LTI_STANDALONE_CLIENT_KEY,
    which we use to LTI determine access type

    `user_credentials` is optional dict with keys "user_id" and "email",
    which we use to test effects of different students being created
    and logged in correctly

    """
    client = oauthlib.oauth1.Client(
        client_key,
        client_secret=settings.PYLTI_CONFIG["consumers"][client_key]["secret"],
        signature_method=oauthlib.oauth1.SIGNATURE_HMAC,
        signature_type=oauthlib.oauth1.SIGNATURE_TYPE_QUERY,
    )

    params = BASE_LTI_PARAMS.copy()

    # Full url instead of relative
    params.update(launch_presentation_return_url="http://scivero.com")

    # required for group creation
    params.update(context_id="myMoodleCourseID")

    # custom parameters
    if teacher_id:
        params.update(custom_teacher_id=teacher_id)
    if assignment_id:
        params.update(custom_assignment_id=assignment_id)
    if question_id:
        params.update(custom_question_id=question_id)
    if user_credentials:
        params.update(user_id=user_credentials["user_id"])
        params.update(
            lis_person_contact_email_primary=user_credentials["email"]
        )

    # any extra parameters
    params.update(**extra_params)

    signature = client.sign(
        "http://testserver/lti/",
        http_method="POST",
        body=urlencode(params),
        headers={
            "Content-Type": oauthlib.oauth1.rfc5849.CONTENT_TYPE_FORM_URLENCODED
        },
    )

    url_parts = urlparse(signature[0])
    query_string = parse_qs(url_parts.query, keep_blank_values=True)
    verify_params = {key: value[0] for key, value in query_string.items()}
    params.update(verify_params)
    request = RequestFactory().post("/lti/", params)
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    return request


class TestViews(TestCase):
    def test_admin_index_wrapper_authenticated(self):
        request = mock.Mock()
        request.user.is_authenticated = True
        response = admin_index_wrapper(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/en/admin/")

    def test_admin_index_wrapper_not_authenticated(self):
        request = mock.Mock()
        request.user.is_authenticated = False
        request.user.teacher.pk = 1
        request.get_host.return_value = "localhost"
        request.META = {}
        response = admin_index_wrapper(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "This component cannot be shown either because your browser does "
            "not seem to accept third-party cookies or your session has "
            "expired",
        )


class TestAccess(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a TOS
        role = Role.objects.get(role="student")
        tos = Tos(version=1, text="Test", current=True, role=role)
        tos.save()

        # Create a teacher
        cls.teacher = Teacher.objects.create(
            user=User.objects.create_user(
                username="teacher",
                email="teacher@mydalite.org",
                password="test",
            )
        )

        # Create a staff user
        cls.staff = User.objects.create_user(
            username="staff",
            email="staff@mydalite.org",
            password="test",
            is_staff=True,
        )

        # Create a superuser
        cls.superuser = User.objects.create_user(
            username="superuser",
            email="superuser@mydalite.org",
            password="test",
            is_superuser=True,
        )

    def test_lti_index_login_required(self):
        # straight GET on url
        response = self.client.get(reverse("student-page-LTI"), follow=True)
        self.assertTemplateUsed("peerinst/login.html")

        # post LTI params on url
        post_data = BASE_LTI_PARAMS
        response = self.client.post("/lti/", post_data)
        self.assertTemplateUsed("peerinst/login.html")

    def test_lti_index_logged_in_as_wrong_user_type(self):
        student_count = Student.objects.count()

        self.client.force_login(self.teacher.user)
        response = self.client.get("/student/lti/", follow=True)
        self.assertTemplateUsed(response, "lti_provider/fail_auth.html")

        assert Student.objects.count() == student_count

    def test_lti_auth_missing_course_id(self):
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
            context_id="",
        )
        response = self.client.post("/lti/", request.POST, follow=True)

        self.assertTemplateUsed(response, "lti_provider/fail_auth.html")
        assert request.user.is_authenticated is False

    def test_lti_auth_new_user_with_email(self):
        # sourcery skip: class-extract-method
        """
        Check that proper lti request results in successful authentication
        """
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
            lis_person_contact_email_primary="new_user@mydalite.org",
        )
        response = LTIRoutingView.as_view()(request)

        assert request.user.is_authenticated is True
        assert request.user is not AnonymousUser
        assert request.user.email == "new_user@mydalite.org"
        assert not request.user.has_usable_password()
        assert response.status_code == 302
        assert response.url.endswith("/student/lti/")
        assert "LTI" in request.session.get("_auth_user_backend")

    def test_lti_auth_new_user_without_email(self):
        """
        Check user creation without email field
        """
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
            lis_person_contact_email_primary="",
        )
        response = LTIRoutingView.as_view()(request)

        assert request.user.is_authenticated is True
        assert request.user is not AnonymousUser
        assert request.user.email == ""
        assert not request.user.has_usable_password()
        assert response.status_code == 302
        assert response.url.endswith("/student/lti/")
        assert "LTI" in request.session.get("_auth_user_backend")

    def test_lti_auth_new_user_without_user_id(self):
        """
        Check user creation without user id
        """
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
            user_id="",
        )
        response = LTIRoutingView.as_view()(request)

        assert request.user.is_authenticated is False
        assert Student.objects.count() == 0
        self.assertTemplateUsed("lti_provider/fail_auth.html")

    def test_lti_auth_teacher_accounts_not_accessible(self):
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
            lis_person_contact_email_primary=self.teacher.user.email,
        )
        response = LTIRoutingView.as_view()(request)

        assert request.user.is_authenticated is True
        assert request.user != self.teacher.user
        assert not request.user.has_usable_password()
        assert request.user.email == self.teacher.user.email

    def test_lti_auth_staff_accounts_not_accessible(self):
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
            lis_person_contact_email_primary=self.staff.email,
        )
        response = LTIRoutingView.as_view()(request)

        assert request.user.is_authenticated is True
        assert request.user.is_staff is False
        assert request.user != self.staff
        assert not request.user.has_usable_password()
        assert request.user.email == self.staff.email

    def test_lti_auth_superuser_accounts_not_accessible(self):
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
            lis_person_contact_email_primary=self.superuser.email,
        )
        response = LTIRoutingView.as_view()(request)

        assert request.user.is_authenticated is True
        assert request.user.is_superuser is False
        assert request.user != self.superuser
        assert not request.user.has_usable_password()
        assert request.user.email == self.superuser.email

    def test_lti_auth_standalone_student_accounts_not_accessible(self):
        student = Student.objects.create(
            student=User.objects.create_user(
                username="student",
                email="student@mydalite.org",
                password="password",
            )
        )

        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
            lis_person_contact_email_primary=student.student.email,
        )
        response = LTIRoutingView.as_view()(request)

        assert request.user.is_authenticated is True
        assert request.user != student.student
        assert not request.user.has_usable_password()
        assert request.user.email == student.student.email

    def test_lti_new_student_show_tos_access_index(self):
        """
        Check that first access by new user results in
        - creation of a new Student
        - redirection to TOS
        - redirection to index if Consent object exists
        """
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY
        )
        response = self.client.post("/lti/", request.POST, follow=True)

        self.assertTemplateUsed(response, "tos/tos_modify.html")
        assert Student.objects.count() == 1

        consent = Consent(
            user=Student.objects.first().student,
            accepted=True,
            tos=Tos.objects.first(),
        )
        consent.save()

        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
        )
        response = self.client.post("/lti/", request.POST, follow=True)

        self.assertTemplateUsed(response, "peerinst/student/index.html")
        assert Student.objects.count() == 1
        assert not hasattr(Student.objects.first().student, "teacher")
        assert response.context["access_lti_standalone"] == True
        assert not response.context.get("access_lti_basic_client_key")
        assert StudentGroup.objects.count() == 1
        assert (
            StudentGroup.objects.first()
            in Student.objects.first().groups.all()
        )

    def test_lti_studentgroup(self):
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY
        )
        response = self.client.post("/lti/", request.POST, follow=True)

        self.assertTemplateUsed(response, "tos/tos_modify.html")
        assert Student.objects.count() == 1

        consent = Consent(
            user=Student.objects.first().student,
            accepted=True,
            tos=Tos.objects.first(),
        )
        consent.save()

        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
            teacher_id=self.teacher.hash,
        )
        response = self.client.post("/lti/", request.POST, follow=True)

        self.assertTemplateUsed(response, "peerinst/student/index.html")
        self.assertContains(
            response, BASE_LTI_PARAMS["lis_person_contact_email_primary"]
        )

        assert Student.objects.count() == 1
        assert (
            StudentGroup.objects.filter(name="myMoodleCourseID").count() == 1
        )
        student = Student.objects.get(
            student__email=BASE_LTI_PARAMS["lis_person_contact_email_primary"]
        )
        assert (
            StudentGroup.objects.get(name="myMoodleCourseID")
            in student.groups.all()
        )
        assert (
            StudentGroup.objects.get(name="myMoodleCourseID")
            in self.teacher.current_groups.all()
        )

    def test_lti_basic_client_key(self):
        # test basic LTI mode
        assignment = Assignment.objects.create(identifier="new_assignment")
        question = Question.objects.create(
            title="physics", text="why is sky blue?"
        )
        assignment.questions.add(question)
        request = generate_lti_request_dalite(
            client_key=settings.LTI_BASIC_CLIENT_KEY,
            teacher_id=self.teacher.hash,
            assignment_id=assignment.identifier,
            question_id=question.pk,
        )
        response = self.client.post("/lti/", request.POST, follow=True)
        consent = Consent(
            user=Student.objects.first().student,
            accepted=True,
            tos=Tos.objects.first(),
        )
        consent.save()

        # log back in after TOS
        request = generate_lti_request_dalite(
            client_key=settings.LTI_BASIC_CLIENT_KEY,
            teacher_id=self.teacher.hash,
            assignment_id=assignment.identifier,
            question_id=question.pk,
        )
        response = self.client.post("/lti/", request.POST, follow=True)
        self.assertTemplateUsed(response, "peerinst/question/start.html")
        assert response.context["access_lti_basic_client_key"] == True
        assert not response.context.get("access_lti_standalone")

    def test_lti_student_wrong_email(self):
        # student 1
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY
        )
        response = self.client.post("/lti/", request.POST, follow=True)
        self.assertTemplateUsed("tos/tos_modify.html")

        # TOS for student 1
        consent = Consent(
            user=Student.objects.first().student,
            accepted=True,
            tos=Tos.objects.first(),
        )
        consent.save()

        # log back in student 1
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY
        )
        response = self.client.post("/lti/", request.POST, follow=True)

        # student 2 who changes their email in LMS to that of student 1
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
            user_credentials={
                "user_id": "wrong_student",
                "email": BASE_LTI_PARAMS["lis_person_contact_email_primary"],
            },
        )
        response = self.client.post("/lti/", request.POST, follow=True)

        # ensure new student gets created, even if emails match
        assert Student.objects.count() == 2

        # TOS for student 2
        consent = Consent(
            user=User.objects.last(),
            accepted=True,
            tos=Tos.objects.first(),
        )
        consent.save()

        # log back in student 2
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
            user_credentials={
                "user_id": "wrong_student",
                "email": BASE_LTI_PARAMS["lis_person_contact_email_primary"],
            },
        )
        response = self.client.post("/lti/", request.POST, follow=True)
        assert Student.objects.count() == 2
        self.assertTemplateUsed("peerinst/student/index.html")

    def test_lti_teacher_lti_login(self):
        # test for myDalite Teacher logging in via LMS LTI
        teacher_credentials = {
            "user_id": self.teacher.user.username,
            "email": self.teacher.user.email,
        }
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
            teacher_id=self.teacher.hash,
            user_credentials=teacher_credentials,
        )
        response = self.client.post("/lti/", request.POST, follow=True)
        self.assertTemplateUsed(response, "tos/tos_modify.html")

        consent = Consent(
            user=Student.objects.get(
                student__email=self.teacher.user.email
            ).student,
            accepted=True,
            tos=Tos.objects.first(),
        )
        consent.save()
        request = generate_lti_request_dalite(
            client_key=settings.LTI_STANDALONE_CLIENT_KEY,
            teacher_id=self.teacher.hash,
            user_credentials=teacher_credentials,
        )
        response = self.client.post("/lti/", request.POST, follow=True)
        self.assertTemplateUsed(response, "peerinst/student/index.html")
        self.assertContains(response, teacher_credentials["email"])
