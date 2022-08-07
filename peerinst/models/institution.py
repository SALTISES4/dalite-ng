from django.db import models
from django.utils.translation import gettext_lazy as _


class Institution(models.Model):
    name = models.CharField(
        max_length=100, unique=True, help_text=_("Name of school.")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("institution")
        verbose_name_plural = _("institutions")


class InstitutionalLMS(models.Model):
    url = models.CharField(
        max_length=100,
        unique=True,
        help_text=_(
            """
            URL found in institutional LMS LTI parameter
            `tool_consumer_instance_guid`.
            """
        ),
    )
    institution = models.ForeignKey(
        Institution, blank=True, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.url

    class Meta:
        verbose_name = _("institution_lms_url")
        verbose_name_plural = _("institution_lms_urls")
