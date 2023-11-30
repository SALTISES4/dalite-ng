import json
import logging

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST, require_safe
from django.views.generic.edit import UpdateView

from dalite.views.errors import response_400, response_500
from peerinst.models import (
    Student,
    StudentAssignment,
    StudentGroup,
    StudentGroupAssignment,
    Teacher,
)

from ..mixins import LoginRequiredMixin, NoStudentsMixin
from .decorators import group_access_required

logger = logging.getLogger("peerinst-views")


def validate_update_data(req):
    try:
        data = json.loads(req.body)
    except ValueError:
        return response_400(req, msg=_("Wrong data type was sent."))

    try:
        name = data["name"]
        value = data["value"]
    except KeyError:
        return response_400(req, msg=_("There are missing parameters."))

    return name, value


@login_required
@require_safe
@group_access_required
def group_details_page(req, group_hash, teacher, group):
    assignments = StudentGroupAssignment.objects.filter(group=group)

    data = {
        "assignments": [
            {
                "url": reverse(
                    "group-assignment",
                    kwargs={"assignment_hash": assignment.hash},
                )
            }
            for assignment in assignments
        ],
        "students": [
            student.pk
            for student in group.students.order_by(
                "student__student__student__email"
            )
        ],
        "urls": {
            "update_url": reverse(
                "group-details-update", kwargs={"group_hash": group.hash}
            ),
            "get_student_information_url": reverse(
                "group-details--student-information"
            ),
        },
    }

    context = {
        "data": json.dumps(data),
        "group": group,
        "assignments": assignments,
        "teacher": teacher,
        # "owned_courses": get_owned_courses(teacher.user),
        # "connected_course": StudentGroupCourse.objects.filter(
        #     student_group=group
        # ).first(),
    }
    # context["is_connected_to_course"] = False
    # if StudentGroupCourse.objects.filter(student_group=group).first():
    #     context["is_connected_to_course"] = True
    #     context["connected_course"] = (
    #         StudentGroupCourse.objects.filter(student_group=group)
    #         .first()
    #         .course
    #     )
    return render(req, "peerinst/group/details.html", context)


@login_required
@require_POST
@group_access_required
def group_details_update(req, group_hash, teacher, group):
    """
    Updates the field of the group using the `name` and `value` given by the
    post request data.

    Parameters
    ----------
    group_hash : str
        Hash of the group
    teacher : Teacher
    group : StudentGroup
        Group corresponding to the hash (returned by `group_access_required`)

    Returns
    -------
    HttpResponse
        Either an empty 200 response if everything worked or an error response
    """

    name, value = validate_update_data(req)
    if isinstance(name, HttpResponse):
        return name

    if name == "name":
        if (
            name != group.name
            and StudentGroup.objects.filter(name=name).exists()
        ):
            return response_400(req, msg=_("That name already exists."))
        group.name = value
        group.save()
        logger.info("Group %d's name was changed to %s.", group.pk, value)

    elif name == "title":
        group.title = value
        group.save()
        logger.info("Group %d's title was changed to %s.", group.pk, value)

    elif name == "teacher":
        try:
            teacher = Teacher.objects.get(user__username=value)
        except Teacher.DoesNotExist:
            return response_400(
                req,
                msg=_(f"There is no teacher with username {teacher}."),
            )
        group.teacher.add(teacher)
        group.save()
        logger.info("Teacher %d was added to group %d.", value, group.pk)

    elif name == "student_id_needed":
        group.student_id_needed = value
        group.save()
        logger.info(
            "Student id needed was set to %s for group %d.", value, group.pk
        )

    else:
        return response_400(req, msg=_("Wrong data type was sent."))

    return HttpResponse(content_type="text/plain")


@login_required
@require_safe
@group_access_required
def group_assignment_page(req, assignment_hash, teacher, group, assignment):
    context = {
        "teacher_id": teacher.id,
        "group": group,
        "assignment": assignment,
        "questions": assignment.questions,
        "students_with_answers": assignment.assignment.answer_set.values_list(
            "user_token", flat=True
        ),
        "data": json.dumps(
            {
                "assignment": {
                    "hash": assignment.hash,
                    "distribution_date": assignment.distribution_date.isoformat()  # noqa
                    if assignment.distribution_date
                    else None,
                },
                "urls": {
                    "get_assignment_student_progress": reverse(
                        "get-assignment-student-progress",
                        kwargs={"assignment_hash": assignment.hash},
                    ),
                    "send_student_assignment": reverse(
                        "send-student-assignment",
                        kwargs={"assignment_hash": assignment.hash},
                    ),
                    "group_assignment_update": reverse(
                        "group-assignment-update",
                        kwargs={"assignment_hash": assignment.hash},
                    ),
                    "distribute_assignment": reverse(
                        "distribute-assignment",
                        kwargs={"assignment_hash": assignment.hash},
                    ),
                },
                "translations": {
                    "distribute": gettext("Distribute"),
                    "distributed": gettext("Distributed"),
                    "distribution_warning": gettext(
                        "Distributing the assignment will send an email to "
                        "all students in the group with a link to the "
                        "assignment."
                    ),
                },
            }
        ),
    }

    return render(req, "peerinst/group/assignment.html", context)


@login_required
@require_POST
@group_access_required
def group_assignment_remove(req, assignment_hash, teacher, group, assignment):
    assignment.delete()
    return HttpResponse()


@login_required
@require_POST
@group_access_required
def group_assignment_update(req, assignment_hash, teacher, group, assignment):
    name, value = validate_update_data(req)
    if isinstance(name, HttpResponse):
        return name

    err = assignment.update(name, value)

    if err is not None:
        return response_400(req, msg=_(err))

    return HttpResponse(content_type="text/plain")


@login_required
@require_POST
@group_access_required
def send_student_assignment(req, assignment_hash, teacher, group, assignment):
    try:
        data = json.loads(req.body)
    except ValueError:
        return response_400(req, msg=_("Wrong data type was sent."))

    try:
        email = data["email"]
    except KeyError:
        return response_400(req, msg=_("There are missing parameters."))

    student = Student.objects.filter(student__email=email).last()
    if student is None:
        return response_400(
            req, msg=_(f'There is no student with email "{email}".')
        )

    student_assignment, __ = StudentAssignment.objects.get_or_create(
        group_assignment=assignment, student=student
    )

    err = student_assignment.send_email("new_assignment")

    if err is not None:
        return response_500(req, msg=_(err))

    return HttpResponse()


@login_required
@require_safe
@group_access_required
def get_assignment_student_progress(
    req, assignment_hash, teacher, group, assignment
):
    data = {"progress": assignment.student_progress}

    return JsonResponse(data)


@login_required
@require_POST
@group_access_required
def distribute_assignment(req, assignment_hash, teacher, group, assignment):
    """
    Distributes the assignment to students.
    """
    assignment.distribute()
    data = {
        "hash": assignment.hash,
        "distribution_date": assignment.distribution_date.isoformat()  # noqa
        if assignment.distribution_date
        else None,
    }
    return JsonResponse(data)


class StudentGroupUpdateView(LoginRequiredMixin, NoStudentsMixin, UpdateView):
    """View for updating group meta-data."""

    model = StudentGroup
    template_name = "peerinst/group/studentgroup_edit.html"
    fields = [
        "title",
        "student_id_needed",
        "semester",
        "year",
        "discipline",
        "institution",
    ]

    def dispatch(self, *args, **kwargs):
        # Check object permissions
        if (
            self.request.user.teacher in self.get_object().teacher.all()
            or self.request.user.is_staff
        ):
            return super().dispatch(*args, **kwargs)
        else:
            raise PermissionDenied

    def get_form(self, form_class=None):
        """
        This is a small convenience to make first available year value satisfy
        the requirement of >= 2015 (for objects with year = 0).
        """
        form = super().get_form(form_class)
        form.fields["year"].widget = forms.NumberInput(attrs={"min": 2015})
        return form

    def get_object(self):
        return StudentGroup.get(self.kwargs["group_hash"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = get_object_or_404(Teacher, user=self.request.user)
        context["teacher"] = teacher
        context["teacher_list"] = list(
            self.get_object().teacher.values("pk", "user__username")
        )
        return context

    def get_success_url(self):
        return reverse("group-details", kwargs=self.kwargs)
