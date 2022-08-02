import logging

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods, require_safe
from django.views.generic import ListView
from django.views.generic.edit import CreateView

from dalite.views.errors import response_400, response_404
from tos.models import Tos

from ..forms import EmailForm, StudentGroupAssignmentForm
from ..mixins import LoginRequiredMixin, NoStudentsMixin
from ..models import (
    Assignment,
    Question,
    Student,
    StudentAssignment,
    StudentGroup,
    StudentGroupAssignment,
    StudentGroupMembership,
    Teacher,
)
from ..students import authenticate_student

logger = logging.getLogger("peerinst-views")


def signup_through_link(request, group_hash):

    # Call logout to ensure a clean session
    logout(request)

    group = StudentGroup.get(group_hash)

    if group is None:
        return response_404(
            request,
            msg=_(
                "The group couldn't be found. Bear in mind that the URL "
                "is case-sensitive."
            ),
        )

    if request.method == "POST":

        form = EmailForm(request.POST)
        if not form.is_valid():
            return response_400(
                request, msg=_("There was a problem with the values sent.")
            )

        student, created = Student.get_or_create(form.cleaned_data["email"])

        if student is None:
            return response_400(
                request,
                msg=_(
                    "There already exists a user with this username. Try a "
                    "different email address."
                ),
            )

        if created:
            student.join_group(group, mail_type="confirmation")
        else:
            student.join_group(group, mail_type="new_group")

        return TemplateResponse(
            request,
            "registration/sign_up_student_done.html",
            context={"student": student, "group": group},
        )

    form = EmailForm()
    tos = Tos.objects.filter(role="student").latest("created").text

    return TemplateResponse(
        request,
        "registration/sign_up_student.html",
        context={"form": form, "group": group, "tos": tos},
    )


@require_safe
def live(request, token, assignment_hash):

    if "LTI" not in request.session.get("_auth_user_backend"):

        # Call logout to ensure a clean session
        logout(request)

        # Login through token
        user, __ = authenticate_student(request, token)
        if isinstance(user, HttpResponse):
            return user
        login(
            request, user, backend="peerinst.backends.CustomPermissionsBackend"
        )

        # Register access type
        request.session["LTI"] = False

    # Get assignment for this token and current question
    group_assignment = StudentGroupAssignment.get(assignment_hash)
    if group_assignment is None:
        return response_404(
            request,
            msg=_(
                "This url doesn't correspond to any assignment. "
                "It may have been deleted by your teacher."
            ),
            logger_msg=(
                "Access to live was tried for unknown assignment with hash "
                "{} by user {}.".format(assignment_hash, user.pk)
            ),
            log=logger.warning,
        )

    group = group_assignment.group
    if group.student_id_needed:
        group_membership = StudentGroupMembership.objects.get(
            student=user.student, group=group
        )
        if not group_membership.student_school_id:
            return HttpResponseRedirect(
                reverse("student-page")
                + "?group-student-id-needed="
                + group.name
            )

    student_assignment = StudentAssignment.objects.get(
        student=user.student, group_assignment=group_assignment
    )

    # Register assignment
    request.session["assignment"] = assignment_hash

    # Register quality
    if group_assignment.quality:
        request.session["quality"] = group_assignment.quality.pk
    elif group_assignment.group.quality:
        request.session["quality"] = group_assignment.group.quality.pk
    elif (
        group_assignment.group.teacher.exists()
        and group_assignment.group.teacher.first().quality
    ):
        request.session[
            "quality"
        ] = group_assignment.group.teacher.first().quality.pk

    assignment = student_assignment.group_assignment
    current_question = student_assignment.get_current_question()
    has_expired = student_assignment.group_assignment.expired

    if has_expired or current_question is None:
        return HttpResponseRedirect(reverse("finish-assignment"))

    questions = assignment.questions
    idx = questions.index(current_question)

    request.session["assignment_first"] = idx == 0
    request.session["assignment_last"] = idx == len(questions) - 1
    request.session["assignment_expired"] = has_expired

    # Redirect to view
    return HttpResponseRedirect(
        reverse(
            "question",
            kwargs={
                "assignment_id": assignment.assignment.pk,
                "question_id": current_question.id,
            },
        )
    )


@login_required
@require_safe
def navigate_assignment(request, assignment_id, question_id, direction, index):

    hash = request.session.get("assignment")
    if hash is None:

        if not Teacher.objects.filter(user=request.user).exists():
            return response_400(
                request,
                msg=_(
                    "Try logging in again using the link to this "
                    "assignment sent via email."
                ),
            )

        assignment = get_object_or_404(Assignment, pk=assignment_id)
        questions = list(
            assignment.questions.order_by("assignmentquestions__rank")
        )
        current_question = get_object_or_404(Question, pk=question_id)
        idx = questions.index(current_question)
        if direction == "next":
            if idx < len(questions) - 1:
                new_question = questions[idx + 1]
            else:
                new_question = questions[0]
        else:
            if idx > 0:
                new_question = questions[idx - 1]
            else:
                new_question = questions[-1]

        # Redirect
        return HttpResponseRedirect(
            reverse(
                "question",
                kwargs={
                    "assignment_id": assignment.pk,
                    "question_id": new_question.id,
                },
            )
        )

    else:

        assignment = StudentGroupAssignment.get(hash)
        question = get_object_or_404(Question, id=question_id)

        if index != "x":
            idx = int(index)
        else:
            idx = None

        new_question = assignment.get_question(
            current_question=question, after=direction == "next", idx=idx
        )

        if new_question is None:
            return HttpResponseRedirect(reverse("student-page"))

        questions = assignment.questions
        idx = questions.index(new_question)

        request.session["assignment_first"] = idx == 0
        request.session["assignment_last"] = idx == len(questions) - 1

        if not request.session["assignment_expired"] and assignment.expired:
            request.session["assignment_expired"] = assignment.expired
            return HttpResponseRedirect(reverse("finish-assignment"))

    # Redirect
    return HttpResponseRedirect(
        reverse(
            "question",
            kwargs={
                "assignment_id": assignment.assignment.pk,
                "question_id": new_question.id,
            },
        )
    )


@login_required
@require_safe
@require_http_methods(["GET"])
def finish_assignment(req):
    try:
        hash_ = req.session["assignment"]
    except KeyError:
        return HttpResponseRedirect(reverse("welcome"))

    assignment = StudentGroupAssignment.get(hash_)
    req.session["assignment_first"] = True
    req.session["assignment_last"] = len(assignment.questions) == 1
    req.session["assignment_expired"] = True

    try:
        student_assignment = StudentAssignment.objects.get(
            student__student=req.user, group_assignment=assignment
        )
        has_expired = assignment.expired and not student_assignment.completed
    except Student.DoesNotExist:
        has_expired = assignment.expired

    context = {
        "assignment_id": assignment.assignment.pk,
        "question_id": assignment.questions[0].id,
        "has_expired": has_expired,
        "conclusion_page": assignment.assignment.conclusion_page,
    }
    return render(req, "peerinst/student/assignment_complete.html", context)


class StudentGroupAssignmentCreateView(
    LoginRequiredMixin, NoStudentsMixin, CreateView
):
    """View to distribute an assignment to a group."""

    model = StudentGroupAssignment
    form_class = StudentGroupAssignmentForm

    def get_form(self):
        form = super().get_form()
        teacher = get_object_or_404(Teacher, user=self.request.user)
        form.fields["group"].queryset = teacher.current_groups.filter(
            Q(mode_created=StudentGroup.STANDALONE)
            | Q(mode_created=StudentGroup.LTI_STANDALONE)
        )

        return form

    def form_valid(self, form):
        # Check teacher owns group
        teacher = get_object_or_404(Teacher, user=self.request.user)
        if teacher not in form.instance.group.teacher.all():
            raise PermissionDenied

        # Attach assignment and save
        form.instance.assignment = get_object_or_404(
            Assignment, pk=self.kwargs["assignment_id"]
        )
        self.object = form.save()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "group-assignment", kwargs={"assignment_hash": self.object.hash}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = get_object_or_404(Teacher, user=self.request.user)
        context["assignment"] = get_object_or_404(
            Assignment, pk=self.kwargs["assignment_id"]
        )
        context["teacher"] = teacher
        return context


class StudentGroupAssignmentListView(
    LoginRequiredMixin, NoStudentsMixin, ListView
):
    model = StudentGroupAssignment
    template_name = "peerinst/teacher/studentgroup_assignments.html"

    def get_queryset(self):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        queryset = StudentGroupAssignment.objects.filter(
            group__teacher=teacher
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = get_object_or_404(Teacher, user=self.request.user)
        context["teacher"] = teacher
        return context
