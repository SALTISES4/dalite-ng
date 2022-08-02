from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AnalyticsConfig(AppConfig):
    name = "analytics"
    verbose_name = _("myDalite analytics")

    def ready(self):
        from . import signals  # noqa
