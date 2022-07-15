import hashlib
import logging

from django.contrib.auth.models import User
from django.db import models

logger = logging.getLogger("tos-models")


class Role(models.Model):
    role = models.CharField(max_length=32, primary_key=True)

    def __str__(self):
        return self.role

    def save(self, *args, **kwargs):
        self.role = self.role.lower()
        super().save(*args, **kwargs)


class Tos(models.Model):
    version = models.PositiveIntegerField()
    hash = models.CharField(max_length=32, editable=False)
    text = models.TextField()
    created = models.DateTimeField(editable=False, auto_now=True)
    current = models.BooleanField()
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.role) + "_" + str(self.version)

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
        super().save(*args, **kwargs)

    @staticmethod
    def get(role, version=None):
        tos = None
        err = None

        if version is None:
            try:
                tos = Tos.objects.get(role__role=role, current=True)
            except Tos.DoesNotExist:
                err = f"No terms of service exist yet for role {role}."
        else:
            try:
                tos = Tos.objects.get(role__role=role, version=version)
            except Tos.DoesNotExist:
                err = (
                    "There is no terms of service with version "
                    "{} for role {}".format(version, role)
                )

        return tos, err


class Consent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tos = models.ForeignKey(Tos, on_delete=models.CASCADE)
    accepted = models.BooleanField()
    datetime = models.DateTimeField(editable=False, auto_now=True)

    @staticmethod
    def get(username, role, version=None, latest=False):
        consent = None

        try:
            role_ = Role.objects.get(role=role)
        except Role.DoesNotExist:
            msg = f"The role {role} doesn't exist yet."
            logger.error(msg)
            raise ValueError(msg)

        if version is None:
            try:
                # returns the latest current consent if `latest` is False
                # or the latest of all consents if `latest` is True
                consent = (
                    Consent.objects.filter(
                        user__username=username,
                        tos__role=role_,
                        tos__current=not latest,
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
                        tos__role=role_,
                        tos__version=version,
                    )
                    .order_by("-datetime")[0]
                    .accepted
                )
            except IndexError:
                consent = None

        return consent

    def __str__(self):
        return (
            "version "
            + str(self.tos.version)
            + " for "
            + str(self.tos.role)
            + " "
            + str(self.user)
        )


class EmailType(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    type = models.CharField(max_length=32)
    title = models.TextField()
    description = models.TextField()
    show_order = models.PositiveIntegerField(blank=True)

    def __str__(self):
        return f"email type {self.type} for {self.role}"

    class Meta:
        unique_together = ("role", "type")

    def save(self, *args, **kwargs):
        if not self.show_order:
            self.show_order = (
                len(
                    EmailType.objects.filter(role=self.role).exclude(
                        type="all"
                    )
                )
                + 1
            )

        if self.type == "all":
            self.show_order = len(EmailType.objects.filter(role=self.role)) + 1

        super().save(*args, **kwargs)


class EmailConsent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email_type = models.ForeignKey(EmailType, on_delete=models.CASCADE)
    accepted = models.BooleanField()
    datetime = models.DateTimeField(editable=False, auto_now=True)

    class Meta:
        get_latest_by = "datetime"

    @staticmethod
    def get(username, role, email_type, default=None, ignore_all=False):
        consent = None

        try:
            consent = (
                EmailConsent.objects.filter(
                    user__username=username,
                    email_type__role=role,
                    email_type__type=email_type,
                )
                .order_by("-datetime")[0]
                .accepted
            )
        except IndexError:
            consent = default

        if not ignore_all and email_type != "all":
            try:
                consent_all = (
                    EmailConsent.objects.filter(
                        user__username=username,
                        email_type__role=role,
                        email_type__type=email_type,
                    )
                    .order_by("-datetime")[0]
                    .accepted
                )
                if not consent_all:
                    consent = False
            except IndexError:
                pass

        return consent

    def __str__(self):
        return f"{self.email_type} for {self.user}"


def _compute_hash(text):
    return hashlib.md5(text.encode()).hexdigest()


def _create_email_type_all(role):
    EmailType.objects.create(
        role=role,
        type="all",
        title="All email",
        description="Turn off all non-administrative email from Dalite.",
        show_order=len(EmailType.objects.filter(role=role)),
    )
