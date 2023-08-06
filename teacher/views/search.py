import bleach
from django.views.generic import TemplateView

from peerinst.models import Discipline, Question, Teacher
from teacher.mixins import TeacherRequiredMixin


class SearchView(TeacherRequiredMixin, TemplateView):
    http_method_names = ["get"]
    model = Teacher
    template_name = "teacher/search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context.update(
            difficulties=[
                [d[0], d[1]] for d in Question.DIFFICULTY_LABELS[:-1]
            ],
            disciplines=[
                bleach.clean(d, tags=[], strip=True).strip()
                for d in Discipline.objects.values_list("title", flat=True)
            ],
            impacts=[[d[0], d[1]] for d in Question.PEER_IMPACT_LABELS[:-1]],
            type=self.request.GET.get("type", ""),
        )
        return context
