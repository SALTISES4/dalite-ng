from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class QualityConfig(AppConfig):
    name = "quality"
    verbose_name = _("Dalite answer quality evaluation")

    def ready(self):
        from . import signals  # noqa
