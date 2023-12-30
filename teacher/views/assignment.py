from django import http
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.views.generic import DetailView, TemplateView

from peerinst.mixins import TOSAcceptanceRequiredMixin
from peerinst.models import Assignment
from teacher.mixins import TeacherRequiredMixin
from tos.models import Consent


class AssignmentCreateView(
    TeacherRequiredMixin, TOSAcceptanceRequiredMixin, TemplateView
):
    """View to serve assignment create template."""

    http_method_names = ["get"]
    template_name = "teacher/assignment/create.html"


class AssignmentUpdateView(TeacherRequiredMixin, DetailView):
    """
    View to serve assignment update template.

    Should for three levels of editability:
    - None at all: non-owners or owners refusing TOS > silently redirect to detail view
    - Meta fields only: owners where assignment.is_editable is false
    - All fields: owners where assignment.is_editable is true
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
        except http.Http404:
            # Object not in queryset, swallow error and redirect to detail view
            return HttpResponseRedirect(
                reverse(
                    "teacher:assignment-detail",
                    args=(self.kwargs.get(self.pk_url_kwarg),),
                )
            )

    def get_queryset(self):
        """Check TOS status, then limit access to a user's own assignments."""
        if not Consent.get(self.request.user.username, "teacher"):
            return Assignment.objects.none()
        else:
            return Assignment.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        assignment = self.get_object()
        context.update(
            LTI_key=str(settings.LTI_BASIC_CLIENT_KEY),
            LTI_secret=str(settings.LTI_BASIC_CLIENT_SECRET),
            LTI_launch_url=str(f"https://{self.request.get_host()}/lti/"),
            meta_editable_by_user=True,
            owner=[u.username for u in assignment.owner.all()],
            questions_editable_by_user=assignment.is_editable,
        )
        return context


class AssignmentDetailView(AssignmentUpdateView):
    """
    Detail view should redirect to update view if accessed by owner and TOS accepted
    """

    def get(self, request, *args, **kwargs):
        # Try to get the object, don't swallow errors
        self.object = self.get_object()
        if request.user in self.object.owner.all() and Consent.get(
            request.user.username, "teacher"
        ):
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
        context.update(
            meta_editable_by_user=False,
            questions_editable_by_user=False,
        )
        return context
