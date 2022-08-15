from unittest import mock
from urllib.parse import parse_qs, urlencode, urlparse

import oauthlib.oauth1
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.db import IntegrityError
from django.test import TestCase
from django.test.client import RequestFactory
from lti_provider.tests.factories import BASE_LTI_PARAMS, generate_lti_request
from lti_provider.views import LTIRoutingView

from dalite.views import admin_index_wrapper
from peerinst.models import Student
from tos.models import Consent, Role, Tos


def generate_lti_request_dalite():
    """
    This code generated valid LTI 1.0 basic-lti-launch-request request
    It is a modified version of lti_provider.tests.factories.generate_lti_request
    but uses PYLTI_CONFIG with consumer LTI_STANDALONE_CLIENT_KEY,
    which we use to LTI determine access type
    """
    client = oauthlib.oauth1.Client(
        settings.LTI_STANDALONE_CLIENT_KEY,
        client_secret=settings.LTI_STANDALONE_CLIENT_SECRET,
        signature_method=oauthlib.oauth1.SIGNATURE_HMAC,
        signature_type=oauthlib.oauth1.SIGNATURE_TYPE_QUERY,
    )

    params = BASE_LTI_PARAMS.copy()
    # Full url instead of relative
    params.update(launch_presentation_return_url="http://scivero.com")
    params.update(context_id="myMoodleCourseID")
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

    def test_lti_auth(self):
        request = generate_lti_request_dalite()
        response = LTIRoutingView.as_view()(request)

        assert request.user.is_authenticated is True
        assert request.user is not AnonymousUser
        assert response.status_code == 302
        assert response.url.endswith("student_lti/")
        assert "LTI" in request.session.get("_auth_user_backend")

    def test_lti_make_student_show_tos_access_index(self):
        request = generate_lti_request_dalite()
        response = self.client.post("/lti/", request.POST, follow=True)

        self.assertTemplateUsed(response, "tos/tos_modify.html")
        assert Student.objects.count() == 1

        consent = Consent(
            user=Student.objects.first().student,
            accepted=True,
            tos=Tos.objects.first(),
        )
        consent.save()

        request = generate_lti_request_dalite()
        response = self.client.post("/lti/", request.POST, follow=True)

        self.assertTemplateUsed(response, "peerinst/student/index.html")
        assert Student.objects.count() == 1
