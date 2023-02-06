import os

from django.conf import settings
from django.views.generic import DetailView

from peerinst.models import SaltiseMember, Teacher
from peerinst.views.views import TeacherBase


class TeacherDashboardView(TeacherBase, DetailView):
    model = Teacher
    template_name = "teacher/dashboard.html"

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
