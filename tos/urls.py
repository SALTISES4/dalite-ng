from csp.decorators import csp_replace
from django.urls import path
from django.views.decorators.clickjacking import xframe_options_exempt

from peerinst.middleware import lti_access_allowed

from . import views

app_name = "tos"
urlpatterns = [
    path("required/", views.tos.tos_required, name="tos_required"),
    path(
        "tos/<role>/<int:version>/update/",
        csp_replace(FRAME_ANCESTORS=["*"])(
            xframe_options_exempt(
                lti_access_allowed(views.tos.tos_consent_update)
            )
        ),
        name="tos_update",
    ),
    path(
        "tos/<role>/<int:version>/modify/",
        csp_replace(FRAME_ANCESTORS=["*"])(
            xframe_options_exempt(
                lti_access_allowed(views.tos.tos_consent_modify)
            )
        ),
        name="tos_modify",
    ),
    path(
        "tos/<role>/modify/",
        csp_replace(FRAME_ANCESTORS=["*"])(
            xframe_options_exempt(
                lti_access_allowed(views.tos.tos_consent_modify)
            )
        ),
        name="tos_modify",
    ),
    path(
        "tos/<role>/<int:version>/",
        csp_replace(FRAME_ANCESTORS=["*"])(
            xframe_options_exempt(lti_access_allowed(views.tos.tos_consent))
        ),
        name="tos_consent",
    ),
    path(
        "tos/<role>/",
        csp_replace(FRAME_ANCESTORS=["*"])(
            xframe_options_exempt(lti_access_allowed(views.tos.tos_consent))
        ),
        name="tos_consent",
    ),
    path(
        "notifications/<role>/modify",
        views.email.email_consent_modify,
        name="email_modify",
    ),
    path(
        "notifications/<role>/update",
        views.email.email_consent_update,
        name="email_update",
    ),
]
