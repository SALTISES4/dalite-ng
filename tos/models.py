from __future__ import unicode_literals

import hashlib

from django.contrib.auth.models import User
from django.db import models


class Tos(models.Model):
    ROLES = ("student", "teacher")
    version = models.PositiveIntegerField()
    hash = models.CharField(max_length=32, editable=False)
    text = models.TextField()
    created = models.DateTimeField(editable=False, auto_now=True)
    current = models.BooleanField()
    role = models.CharField(
        max_length=2, choices=tuple((role[:2], role) for role in ROLES)
    )

    class Meta:
        unique_together = (("role", "version"), ("role", "hash"))

    def save(self, *args, **kwargs):
        if not self.pk:
            self.hash = _compute_hash(str(self.text))
        if self.current:
            Tos.objects.filter(role=self.role, current=True).update(
                current=False
            )
        elif not Tos.objects.filter(role=self.role):
            self.current = True
        super(Tos, self).save(*args, **kwargs)

    @staticmethod
    def get(role, version=None):
        assert isinstance(role, basestring) and role in (
            list(Tos.ROLES) + [r[:2] for r in Tos.ROLES]
        ), "Precondition failed for `role`"
        assert version is None or (
            isinstance(version, int) and version >= 0
        ), "Precondition failed for `version`"

        tos = None
        err = None

        role = role[:2]
        role_long = [r for r in Tos.ROLES if r.startswith(role)][0]

        if version is None:
            try:
                tos = Tos.objects.get(role=role, current=True)
            except Tos.DoesNotExist:
                err = 'No terms of service exist yet for role "{}".'.format(
                    role_long
                )
        else:
            try:
                tos = Tos.objects.get(role=role, version=version)
            except Tos.DoesNotExist:
                err = (
                    "There is no terms of service with version "
                    '{} for role "{}"'.format(version, role_long)
                )

        output = (tos, err)
        assert (
            isinstance(output, tuple)
            and len(output) == 2
            and (output[0] is None) != (output[1] is None)
        ), "Postcondition failed"
        return output


class Consent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tos = models.ForeignKey(Tos, on_delete=models.CASCADE)
    accepted = models.BooleanField()
    datetime = models.DateTimeField(editable=False, auto_now=True)

    @staticmethod
    def get(username, role, version=None):
        assert isinstance(
            username, basestring
        ), "Precondition failed for `username`"
        assert isinstance(role, basestring) and role in (
            list(Tos.ROLES) + [r[:2] for r in Tos.ROLES]
        ), "Precondition failed for `role`"
        assert version is None or (
            isinstance(version, int) and version >= 0
        ), "Precondition failed for `version`"

        consent = None

        role = role[:2]

        if version is None:
            try:
                consent = (
                    Consent.objects.filter(
                        user__username=username,
                        tos__role=role,
                        tos__current=True,
                    )
                    .order_by("-datetime")[0]
                    .accepted
                )
            except IndexError:
                consent = None
        else:
            try:
                consent = (
                    Consent.objects.filter(
                        user__username=username,
                        tos__role=role,
                        tos__version=version,
                    )
                    .order_by("-datetime")[0]
                    .accepted
                )
            except IndexError:
                consent = None

        output = consent
        assert output is None or isinstance(
            output, bool
        ), "Postcondition failed"
        return output


def _compute_hash(text):
    assert isinstance(text, basestring)
    output = hashlib.md5(text.encode()).hexdigest()
    assert isinstance(output, basestring) and len(output) == 32
    return output
