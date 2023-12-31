from django.views.generic import DetailView, TemplateView

from peerinst.mixins import TOSAcceptanceRequiredMixin
from peerinst.models import Question
from teacher.mixins import TeacherRequiredMixin


class QuestionCreateView(
    TeacherRequiredMixin, TOSAcceptanceRequiredMixin, TemplateView
):
    http_method_names = ["get"]
    template_name = "teacher/question/create_update.html"


class QuestionCopyView(
    TeacherRequiredMixin, TOSAcceptanceRequiredMixin, DetailView
):
    http_method_names = ["get"]
    template_name = "teacher/question/create_update.html"
    queryset = Question.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context.update(
            copy=True,
        )
        return context


class QuestionUpdateView(
    TeacherRequiredMixin, TOSAcceptanceRequiredMixin, DetailView
):
    http_method_names = ["get"]
    template_name = "teacher/question/create_update.html"

    def get_queryset(self):
        """Same as REST endpoint"""
        return Question.editable_queryset_for_user(self.request.user)
