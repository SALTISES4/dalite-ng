from django.views.generic import TemplateView

from teacher.mixins import TeacherRequiredMixin


class GroupCreateView(TeacherRequiredMixin, TemplateView):
    http_method_names = ["get"]
    template_name = "teacher/group/create.html"
