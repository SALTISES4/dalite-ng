import os

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test

from peerinst.models import SaltiseMember


class TeacherRequiredMixin:
    """User must be logged in and have a Teacher account."""

    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return login_required(
            user_passes_test(
                lambda user: hasattr(user, "teacher"),
                login_url="/access_denied/",
            )(view)
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
