from unittest import mock

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.db import IntegrityError
from django.test import TestCase
from lti_provider.tests.factories import generate_lti_request
from lti_provider.views import LTIRoutingView

from dalite.views import admin_index_wrapper
from peerinst.models import Student
from tos.models import Consent, Role, Tos


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
    def test_lti_auth(self):
        request = generate_lti_request()
        response = LTIRoutingView.as_view()(request)

        assert request.user.is_authenticated is True
        assert request.user is not AnonymousUser
        assert response.status_code == 302
        assert response.url.endswith("student_lti/")
        assert "LTI" in request.session.get("_auth_user_backend")

    def test_lti_make_student(self):
        # Create a TOS
        role = Role.objects.get(role="student")
        tos = Tos(version=1, text="Test", current=True, role=role)
        tos.save()

        request = generate_lti_request()
        response = self.client.post("/lti/", request.POST, follow=True)

        self.assertTemplateUsed(response, "tos/tos_modify.html")
        assert Student.objects.count() == 1

        # Add consent
        consent = Consent(
            user=Student.objects.first().student,
            accepted=True,
            tos=Tos.objects.first(),
        )
        consent.save()

        request = generate_lti_request()
        params = dict(request.POST)
        params.update(
            {
                "launch_presentation_return_url": "scivero.com",
            }
        )
        response = self.client.post("/lti/", params, follow=True)

        assert Student.objects.count() == 1
