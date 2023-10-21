from django.views.generic import TemplateView

from peerinst.views.views import TeacherBase


class LibraryView(TeacherBase, TemplateView):
    http_method_names = ["get"]
    template_name = "teacher/library.html"
