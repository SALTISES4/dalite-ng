import json
import re
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST, require_safe

from dalite.views.errors import response_400, response_500
from dalite.views.utils import get_json_params
from peerinst.models import (
    Student,
    StudentAssignment,
    StudentGroup,
    StudentGroupAssignment,
    Teacher,
    StudentGroupCourse,
)

from .decorators import group_access_required
from reputation.models import ReputationType

from course_flow.views import get_owned_courses

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

    student_reputation_criteria = [
        dict(c)
        for c in ReputationType.objects.get(type="student").criteria.all()
    ]

    context = {
        "data": json.dumps(data),
        "group": group,
        "assignments": assignments,
        "teacher": teacher,
        "student_reputation_criteria": [
            {
                "name": c["name"],
                "icon": c["badge_icon"],
                "colour": c["badge_colour"],
                "description": ugettext(
                    re.sub(
                        r"\bYou\b",
                        "They",
                        re.sub(r"\byou\b", "they", c["description"]),
                    )
                ),
            }
            for c in student_reputation_criteria
        ],
        "owned_courses": get_owned_courses(teacher.user),
        "connected_course": StudentGroupCourse.objects.filter(
            student_group=group
        ).first(),
        "LTI_key": str(settings.LTI_CLIENT_KEY),
        "LTI_secret": str(settings.LTI_CLIENT_SECRET),
        "LTI_launch_url": str("https://" + req.get_host() + "/lti/"),
    }
    context["is_connected_to_course"] = False
    if StudentGroupCourse.objects.filter(student_group=group).first():
        context["is_connected_to_course"] = True
        context["connected_course"] = (
            StudentGroupCourse.objects.filter(student_group=group)
            .first()
            .course
        )
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
                msg=_("There is no teacher with username {}.".format(teacher)),
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
                    "distribute": ugettext("Distribute"),
                    "distributed": ugettext("Distributed"),
                    "distribution_warning": ugettext(
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
            req, msg=_('There is no student with email "{}".'.format(email))
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


@login_required
@require_POST
def get_student_reputation(req):
    """
    Returns the student information along with the convincing rationales
    criterion.

    Parameters
    ----------
    req : HttpRequest
        Request with:
            parameters:
                id: int
                    Student pk

    Returns
    -------
    Either
        JSONResponse
            Response with json data:
                {
                    email : str
                        Student email
                    last_login : str
                        Date of last login in isoformat
                    popularity : float
                        Value of the convincing rationales criterion

                }
        HttpResponse
            Error response
    """
    args = get_json_params(req, args=["id"])
    if isinstance(args, HttpResponse):
        return args
    (id_,), _ = args

    try:
        student = Student.objects.get(pk=id_)
    except Student.DoesNotExist:
        return response_400(
            req,
            msg=_("The student couldn't be found."),
            logger_msg=(
                "The student with pk {} couldn't be found.".format(id_)
            ),
            log=logger.warning,
        )
    criteria = {
        c.name: student.evaluate_reputation(c.name)
        for c in ReputationType.objects.get(type="student").criteria.all()
    }

    return JsonResponse(
        {
            "email": student.student.email,
            "last_login": student.student.last_login.isoformat()
            if student.student.last_login is not None
            else None,
            "criteria": criteria,
        }
    )
