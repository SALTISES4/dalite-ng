from django.conf.urls import url
from . import views

app_name = "tos"
urlpatterns = [
    url(
        r"(?P<role>\w{1,})/(?P<version>\d{1,})/update/$",
        views.consent_update,
        name="update",
    ),
    url(
        r"(?P<role>\w{1,})/(?P<version>\d{1,})/modify/$",
        views.consent_modify,
        name="modify",
    ),
    url(
        r"(?P<role>\w{1,})/(?P<version>\d{1,})/$",
        views.consent,
        name="consent",
    ),
    url(
        r"(?P<role>\w{1,})/$",
        views.consent,
        name="consent",
    ),
]
