from django.views.generic import TemplateView

from peerinst.models import StudentGroup
from teacher.mixins import TeacherRequiredMixin


class GroupCreateView(TeacherRequiredMixin, TemplateView):
    http_method_names = ["get"]
    template_name = "teacher/group/create.html"


class GroupUpdateView(TeacherRequiredMixin, TemplateView):
    http_method_names = ["get"]
    model = StudentGroup
    template_name = "teacher/group/update.html"
