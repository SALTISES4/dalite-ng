import logging
from urllib.parse import urlparse

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import OperationalError
from django.utils.translation import gettext_lazy as _


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
