from csp.decorators import csp_exempt
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import render
from django.urls import path

from peerinst.middleware import lti_access_allowed
from peerinst.tests.test_lti import generate_lti_request_dalite

from .urls import urlpatterns


def lti_consumer(request):
    """
    View to mock an LMS
    """
    logout(request)
    request = generate_lti_request_dalite(
        client_key=settings.LTI_STANDALONE_CLIENT_KEY,
        server="http://127.0.0.1:8000/lti/",
        # custom_question_id=740,
        # custom_assignment_id="id3",
    )

    return render(
        request, "peerinst/lti_consumer.html", {"data": request.POST}
    )


urlpatterns = urlpatterns + [
    path(
        "lti_consumer/",
        csp_exempt(lti_access_allowed(lti_consumer)),
        name="lti-consumer",
    )
]
