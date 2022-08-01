from django.db import models
from django.utils.translation import ugettext_lazy as _


class FakeUsername(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = _("fake username")
        verbose_name_plural = _("fake usernames")


class FakeCountry(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = _("fake country")
        verbose_name_plural = _("fake countries")


class LtiEvent(models.Model):
    question_id = models.IntegerField(blank=True, null=True)
    assignment_id = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    event_type = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return str(self.timestamp)
