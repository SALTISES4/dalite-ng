import logging
from urllib.parse import urlparse

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import OperationalError
from django.utils.translation import gettext_lazy as _

OPTIONAL_COOKIES = []
REQUIRED_COOKIES = ["csrftoken", "sessionid", "django_language"]


class PeerinstConfig(AppConfig):
    name = "peerinst"
    verbose_name = _("Dalite Peer Instruction")
    required_settings = [
        "DEFAULT_SCHEME_HOST_PORT",
    ]

    def ready(self):

        import peerinst.signals  # noqa

        from .scheduled import start_scheduled_events

        try:
            start_scheduled_events()
        except OperationalError:
            logging.getLogger("peerinst-scheduled").warning(
                "The migrations have to be run before the scheduled event "
                "may work."
            )

        for setting in self.required_settings:
            if (
                not hasattr(settings, setting)
                or getattr(settings, setting) == ""
            ):
                raise ImproperlyConfigured(
                    f"{setting} {_('missing from settings.py')}"
                )

        _url = urlparse(settings.DEFAULT_SCHEME_HOST_PORT)
        if _url.hostname not in settings.ALLOWED_HOSTS:
            raise ImproperlyConfigured(
                f"{_url.netloc} is not in ALLOWED_HOSTS"
            )

        # Ensure required cookies are created
        from cookie_consent.models import Cookie, CookieGroup  # noqa

        required_cookie_group, _created = CookieGroup.objects.get_or_create(
            name="Required cookies",
            varname="required",
            is_required=True,
            is_deletable=False,
        )
        optional_cookie_group, _created = CookieGroup.objects.get_or_create(
            name="Optional cookies",
            varname="optional",
            is_required=False,
            is_deletable=True,
        )
        for cookie in REQUIRED_COOKIES:
            Cookie.objects.get_or_create(
                cookiegroup=required_cookie_group,
                name=cookie,
                domain=settings.ALLOWED_HOSTS[0],
            )
        for cookie in OPTIONAL_COOKIES:
            Cookie.objects.get_or_create(
                cookiegroup=optional_cookie_group,
                name=cookie,
                domain=settings.ALLOWED_HOSTS[0],
            )
