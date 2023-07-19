import bleach
from django.views.generic import DetailView, TemplateView

from peerinst.models import Assignment, Discipline, Question, Teacher
from peerinst.views.views import TeacherBase
from teacher.mixins import TeacherRequiredMixin


class TeacherDashboardView(TeacherBase, DetailView):
    model = Teacher
    template_name = "teacher/dashboard.html"


class LibraryView(TeacherBase, TemplateView):
    http_method_names = ["get"]
    template_name = "teacher/library.html"


class AssignmentCreateView(TeacherRequiredMixin, TemplateView):
    http_method_names = ["get"]
    template_name = "teacher/assignment/create.html"


class AssignmentDetailView(TeacherRequiredMixin, DetailView):
    http_method_names = ["get"]
    model = Assignment
    pk_url_kwarg = "identifier"
    queryset = Assignment.objects.all()  # Limit to 'valid' assignments?
    template_name = "teacher/assignment/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        assignment = self.get_object()
        context.update(
            owner=[u.username for u in assignment.owner.all()],
        )
        return context


class AssignmentUpdateView(TeacherRequiredMixin, DetailView):
    """
    Update view should account for three levels of editability:
    - None at all: non-owners >>> get_queryset will yield 404
    - Meta fields only: owners where assignment.editable is false
    - All fields: owners where assignment.editable is true
    """

    http_method_names = ["get"]
    model = Assignment
    pk_url_kwarg = "identifier"
    template_name = "teacher/assignment/update.html"

    def get_queryset(self):
        """
        Limit access to a user's own assignments
        """
        return Assignment.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        assignment = self.get_object()
        user_is_owner = self.request.user in assignment.owner.all()
        context.update(
            editable=assignment.editable,
            owner=[u.username for u in assignment.owner.all()],
        )
        return context


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
