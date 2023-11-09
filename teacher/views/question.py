from django.db.models import Exists, OuterRef, Q
from django.views.generic import DetailView, TemplateView

from peerinst.models import Answer, Question
from teacher.mixins import TeacherRequiredMixin


class QuestionCreateView(TeacherRequiredMixin, TemplateView):
    http_method_names = ["get"]
    template_name = "teacher/question/create_update.html"


class QuestionUpdateView(TeacherRequiredMixin, DetailView):
    http_method_names = ["get"]
    template_name = "teacher/question/create_update.html"

    def get_queryset(self):
        """
        Same queryset as REST endpoint
        """
        queryset = Question.objects.filter(
            Q(user=self.request.user) | Q(collaborators=self.request.user)
        )

        answers = (
            Answer.objects.filter(question=OuterRef("pk"))
            .exclude(expert=True)
            .exclude(user_token__exact="")
            .exclude(user_token__exact=OuterRef("user__username"))
        )
        queryset = queryset.filter(~Exists(answers)).distinct()

        return queryset
