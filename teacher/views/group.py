from django.views.generic import DetailView, TemplateView

from peerinst.models import StudentGroup
from teacher.mixins import TeacherRequiredMixin


class GroupCreateView(TeacherRequiredMixin, TemplateView):
    http_method_names = ["get"]
    template_name = "teacher/group/create.html"


class GroupUpdateView(TeacherRequiredMixin, DetailView):
    http_method_names = ["get"]
    model = StudentGroup
    template_name = "teacher/group/update.html"

    def get_queryset(self):
        return StudentGroup.objects.filter(teacher__user=self.request.user)

    def get_object(self):
        return StudentGroup.get(self.kwargs.get("hash"))
