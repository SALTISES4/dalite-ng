from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReputationConfig(AppConfig):
    name = "reputation"
    verbose_name = _("Dalite reputation framework")

    def ready(self):
        from . import signals  # noqa
