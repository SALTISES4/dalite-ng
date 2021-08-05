from django.urls import path

from . import views

app_name = "tos"
urlpatterns = [
    path("required/", views.tos.tos_required, name="tos_required"),
    path(
        "tos/<role>/<int:version>/update/",
        views.tos.tos_consent_update,
        name="tos_update",
    ),
    path(
        "tos/<role>/<int:version>/modify/",
        views.tos.tos_consent_modify,
        name="tos_modify",
    ),
    path(
        "tos/<role>/modify/",
        views.tos.tos_consent_modify,
        name="tos_modify",
    ),
    path(
        "tos/<role>/<int:version>/",
        views.tos.tos_consent,
        name="tos_consent",
    ),
    path(
        "tos/<role>/",
        views.tos.tos_consent,
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
