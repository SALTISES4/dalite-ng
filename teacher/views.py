import bleach
from django import http
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
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


class AssignmentUpdateView(TeacherRequiredMixin, DetailView):
    """
    Update view should account for three levels of editability:
    - None at all: non-owners >>> redirect to view only
    - Meta fields only: owners where assignment.editable is false
    - All fields: owners where assignment.editable is true
    """

    http_method_names = ["get"]
    model = Assignment
    pk_url_kwarg = "identifier"
    template_name = "teacher/assignment/update.html"

    def get(self, request, *args, **kwargs):
        try:
            # Try to get the object
            self.get_object()
            return super().get(request, *args, **kwargs)
        except http.Http404 as e:
            # Object is not in queryset, swallow error and redirect to detail view
            return HttpResponseRedirect(
                reverse(
                    "teacher:assignment-detail",
                    args=(self.kwargs.get(self.pk_url_kwarg),),
                )
            )

    def get_queryset(self):
        """
        Limit access to a user's own assignments
        """
        return Assignment.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        assignment = self.get_object()
        context.update(
            meta_editable_by_user=True,
            questions_editable_by_user=assignment.editable,
            owner=[u.username for u in assignment.owner.all()],
        )
        return context


class AssignmentDetailView(AssignmentUpdateView):
    """
    Detail view should redirect to update view if accessed by owner
    """

    def get(self, request, *args, **kwargs):
        # Try to get the object, don't swallow errors
        self.object = self.get_object()
        if request.user in self.object.owner.all():
            return HttpResponseRedirect(
                reverse(
                    "teacher:assignment-update",
                    args=(self.kwargs.get(self.pk_url_kwarg),),
                )
            )
        # Don't call super! ;)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_queryset(self):
        return Assignment.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        assignment = self.get_object()
        context.update(
            meta_editable_by_user=False,
            questions_editable_by_user=False,
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
