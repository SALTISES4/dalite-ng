import os

from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import reverse

from peerinst.models import SaltiseMember
from tos.models import Consent


class TeacherRequiredMixin(UserPassesTestMixin):
    """
    User must be logged in, have a Teacher account, and a current TOS.
    """

    def get_latest_teacher_consent(self, username):
        return (
            Consent.objects.filter(
                user__username=username,
                tos__role="teacher",
            )
            .order_by("-datetime")
            .first()
        )

    def test_func(self):
        if not hasattr(self.request.user, "teacher"):
            return False

        latest_teacher_consent = self.get_latest_teacher_consent(
            self.request.user.username
        )
        if (
            not latest_teacher_consent
            or not latest_teacher_consent.tos.current
        ):
            return False

        return True

    def handle_no_permission(self):
        if not hasattr(self.request.user, "teacher"):
            raise PermissionDenied()

        latest_teacher_consent = self.get_latest_teacher_consent(
            self.request.user.username
        )
        if (
            not latest_teacher_consent
            or not latest_teacher_consent.tos.current
        ):
            return HttpResponseRedirect(
                reverse("tos:tos_modify", args=("teacher",))
                + "?next="
                + reverse("teacher", args=(self.request.user.teacher.pk,))
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        backup_avatar = os.path.join(
            settings.STATIC_URL, "components/img/logo.gif"
        )
        try:
            if self.request.user.saltisemember.picture:
                context["avatar"] = self.request.user.saltisemember.picture.url
            else:
                context["avatar"] = backup_avatar
        except SaltiseMember.DoesNotExist:
            context["avatar"] = backup_avatar
        return context
