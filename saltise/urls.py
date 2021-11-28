from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import path
from django.views.generic.base import TemplateView

app_name = "saltise"


def not_authenticated(user):
    return not user.is_authenticated


def is_teacher(user):
    return hasattr(user, "teacher")


urlpatterns = [
    path(
        "login/",
        user_passes_test(
            not_authenticated,
            login_url="/saltise/lobby/",
            redirect_field_name=None,
        )(auth_views.LoginView.as_view(template_name="saltise/login.html")),
        name="login",
    ),
    path(
        "lobby/",
        login_required()(
            user_passes_test(is_teacher)(
                TemplateView.as_view(template_name="saltise/lobby.html")
            )
        ),
        name="lobby",
    ),
]
