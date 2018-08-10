# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
    require_safe,
)
from django.views.generic import ListView
from django.views.generic.edit import CreateView

from ..forms import EmailForm, StudentGroupAssignmentForm
from ..mixins import LoginRequiredMixin, NoStudentsMixin
from ..models import (
    Assignment,
    Question,
    Student,
    StudentAssignment,
    StudentGroup,
    StudentGroupAssignment,
    Teacher,
)
from ..students import authenticate_student, verify_student_token
from ..util import get_object_or_none


def signup_through_link(request, group_hash):

    # Call logout to ensure a clean session
    logout(request)

    group = StudentGroup.get(group_hash)

    if group is None:
        raise Http404()
    else:
        if request.method == "POST":
            form = EmailForm(request.POST)
            if form.is_valid():

                student = Student.get_or_create(form.cleaned_data["email"])

                if student is None:
                    resp = TemplateResponse(
                        req,
                        "400.html",
                        context={
                            "message": _(
                                "There already exists a user with this "
                                "username. Try a different email address."
                            )
                        },
                    )
                    return HttpResponseBadRequest(resp.render())

                else:

                    student.send_confirmation_email(group, request.get_host())

                    return TemplateResponse(
                        request,
                        "registration/sign_up_student_done.html",
                        context={"student": student, "group": group},
                    )

        else:
            form = EmailForm()

        return TemplateResponse(
            request,
            "registration/sign_up_student.html",
            context={"form": form, "group": group},
        )


@require_safe
def confirm_signup_through_link(request, group_hash, token):

    # Call logout to ensure a clean session
    logout(request)

    # Validate token and activate account
    username, email, err = verify_student_token(token)
    group = StudentGroup.get(group_hash)

    if group is None:
        raise Http404()

    if username is not None:
        student = get_object_or_404(Student, student__username=username)
        student.student.is_active = True
        student.groups.add(group)
        student.save()

        return TemplateResponse(
            request,
            "registration/sign_up_student_confirmation.html",
            context={"group": group},
        )
    else:
        raise PermissionDenied


@require_safe
def live(request, token, assignment_hash):

    # Call logout to ensure a clean session
    logout(request)

    # Login through token
    user = authenticate_student(token)
    login(request, user)

    # Register access type
    request.session["nonLTI"] = True

    # Get assignment for this token and current question
    group_assignment = StudentGroupAssignment.get(assignment_hash)
    student_assignment = StudentAssignment.objects.get(
        student=user.student, group_assignment=group_assignment
    )

    # Register assignment
    request.session["assignment"] = assignment_hash

    # Redirect to view
    return HttpResponseRedirect(
        reverse(
            "question",
            kwargs={
                "assignment_id": student_assignment.group_assignment.assignment.pk,
                "question_id": student_assignment.get_current_question().id,
            },
        )
    )


@login_required
@require_safe
def navigate_assignment(request, assignment_id, question_id, direction, index):

    assignment = StudentGroupAssignment.get(request.session["assignment"])
    question = get_object_or_404(Question, id=question_id)

    new_question = assignment.get_question(
        current_question=question, after=direction == "next"
    )

    if new_question is None:
        raise Http404()

    # Redirect
    return HttpResponseRedirect(
        reverse(
            "question",
            kwargs={
                "assignment_id": assignment_id,
                "question_id": new_question.id,
            },
        )
    )


class StudentGroupAssignmentCreateView(
    LoginRequiredMixin, NoStudentsMixin, CreateView
):
    """View to distribute an assignment to a group."""

    model = StudentGroupAssignment
    form_class = StudentGroupAssignmentForm

    def get_form(self):
        form = super(StudentGroupAssignmentCreateView, self).get_form()
        teacher = get_object_or_404(Teacher, user=self.request.user)
        form.fields["group"].queryset = teacher.current_groups.all()

        return form

    def form_valid(self, form):
        # Attach assignment and save
        form.instance.assignment = get_object_or_404(
            Assignment, pk=self.kwargs["assignment_id"]
        )
        self.object = form.save()

        # Dispatch e-mails
        self.object.send_assignment_emails(self.request.get_host())

        return super(StudentGroupAssignmentCreateView, self).form_valid(form)

    def get_success_url(self):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        return reverse("group-assignments", kwargs={"teacher_id": teacher.pk})

    def get_context_data(self, **kwargs):
        context = super(
            StudentGroupAssignmentCreateView, self
        ).get_context_data(**kwargs)
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
    template_name = "peerinst/teacher_studentgroup_assignments.html"

    def get_queryset(self):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        queryset = StudentGroupAssignment.objects.filter(
            group__teacher=teacher
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super(StudentGroupAssignmentListView, self).get_context_data(
            **kwargs
        )
        teacher = get_object_or_404(Teacher, user=self.request.user)
        context["teacher"] = teacher
        return context
