from django.views.generic import DetailView

from peerinst.models import Teacher
from peerinst.views.views import TeacherBase


class TeacherDashboardView(TeacherBase, DetailView):
    model = Teacher
    template_name = "teacher/dashboard.html"
