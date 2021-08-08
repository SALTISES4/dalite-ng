from django.urls import path

from peerinst.middleware import lti_access_allowed

from . import views

app_name = "tos"
urlpatterns = [
    path("required/", views.tos.tos_required, name="tos_required"),
    path(
        "tos/<role>/<int:version>/update/",
        lti_access_allowed(views.tos.tos_consent_update),
        name="tos_update",
    ),
    path(
        "tos/<role>/<int:version>/modify/",
        lti_access_allowed(views.tos.tos_consent_modify),
        name="tos_modify",
    ),
    path(
        "tos/<role>/modify/",
        lti_access_allowed(views.tos.tos_consent_modify),
        name="tos_modify",
    ),
    path(
        "tos/<role>/<int:version>/",
        lti_access_allowed(views.tos.tos_consent),
        name="tos_consent",
    ),
    path(
        "tos/<role>/",
        lti_access_allowed(views.tos.tos_consent),
        name="tos_consent",
    ),
    path(
        "email/<role>/modify",
        views.email.email_consent_modify,
        name="email_modify",
    ),
    path(
        "email/<role>/update",
        views.email.email_consent_update,
        name="email_update",
    ),
    path(
        "email/<role>/change",
        views.email.change_user_email,
        name="email_change",
    ),
]
