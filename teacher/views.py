from django.views.generic import DetailView, TemplateView

from peerinst.models import Teacher
from peerinst.views.views import TeacherBase


class TeacherDashboardView(TeacherBase, DetailView):
    model = Teacher
    template_name = "teacher/dashboard.html"


class SearchView(TeacherBase, DetailView):
    http_method_names = ["get"]
    model = Teacher
    template_name = "teacher/search.html"


class LibraryView(TeacherBase, TemplateView):
    http_method_names = ["get"]
    template_name = "teacher/library.html"
