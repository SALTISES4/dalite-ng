import bleach
from django.views.generic import DetailView, TemplateView

from peerinst.models import Discipline, Question, Teacher
from peerinst.views.views import TeacherBase


class TeacherDashboardView(TeacherBase, DetailView):
    model = Teacher
    template_name = "teacher/dashboard.html"


class SearchView(TeacherBase, DetailView):
    http_method_names = ["get"]
    model = Teacher
    template_name = "teacher/search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context.update(
            difficulties=[[d[0], d[1]] for d in Question.DIFFICULTY_LABELS],
            disciplines=[
                bleach.clean(d, tags=[], strip=True).strip()
                for d in Discipline.objects.values_list("title", flat=True)
            ],
            impacts=[[d[0], d[1]] for d in Question.PEER_IMPACT_LABELS],
        )
        return context


class LibraryView(TeacherBase, TemplateView):
    http_method_names = ["get"]
    template_name = "teacher/library.html"
