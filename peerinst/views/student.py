import json
import logging
import re

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST, require_safe

from dalite.views.errors import response_400, response_403
from tos.models import Consent

from ..lti import manage_LTI_studentgroup
from ..models import (
    Student,
    StudentAssignment,
    StudentGroup,
    StudentGroupAssignment,
    StudentGroupMembership,
    StudentNotification,
)
from ..students import (
    authenticate_student,
    create_student_token,
    get_student_username_and_password,
)
from .decorators import student_required

logger = logging.getLogger("peerinst-auth")


def validate_group_data(req):
    """
    Checks if the request is a well formed json, contains the data to get group
    information and the group exists.  The group is obtained with either a
    field `group_name` or `group_link`.

    Returns
    -------
    Either:
    StudentGroup
        Student and group corresponding for the request
    HttpResponse
        Response corresponding to the obtained error
    """
    try:
        data = json.loads(req.body)
    except ValueError:
        return response_400(
            req,
            msg=_("Wrong data type was sent."),
            logger_msg=("The sent data wasn't in a valid JSON format."),
            log=logger.warning,
        )

    try:
        group_name = data["group_name"].strip()
        group_link = None
    except KeyError:
        try:
            group_link = data["group_link"].strip()
            group_name = None
        except KeyError:
            return response_400(
                req,
                msg=_("There are missing parameters."),
                logger_msg=(
                    "The arguments 'group_name' or 'group_link' were missing."
                ),
                log=logger.warning,
            )

    if group_name is None:
        try:
            hash_ = re.match(
                rf"^{req.scheme}://[^/]+/\w*/live/signup/form/([0-9A-Za-z=_-]+)$",  # noqa E501
                group_link,
            ).group(1)
        except AttributeError:
            return response_400(
                req,
                msg=_(
                    "There pas an error parsing the sent link. Please try "
                    "again."
                ),
                logger_msg=(
                    "A student signup was tried with the link %s.",
                    group_link,
                ),
                log=logger.warning,
            )
        group = StudentGroup.get(hash_)
        if group is None:
            return response_400(
                req,
                msg=_(
                    "There doesn't seem to be any group corresponding to"
                    "the link. Please try again."
                ),
                logger_msg=(
                    "There is no group corresponding to the hash %s.",
                    hash_,
                ),
                log=logger.warning,
            )

    else:
        try:
            group = StudentGroup.objects.get(name=group_name)
        except StudentGroup.DoesNotExist:
            return response_403(
                req,
                msg=_(
                    "The group doesn't seem to exist. Refresh the page "
                    "and try again"
                ),
                logger_msg=(
                    "There is no group corresponding to the name %s.",
                    group_name,
                ),
                log=logger.warning,
            )

    return group


def login_student(req, token=None):
    if token is None:
        if not isinstance(req.user, User):
            return (
                response_403(
                    req,
                    msg=_(
                        "You must be a logged in student to access this "
                        "resource."
                    ),
                    logger_msg=(
                        "Student index page accessed without a token or being "
                        "logged in."
                    ),
                    log=logger.warning,
                ),
                None,
            )
        user = req.user
    else:
        user = authenticate_student(req, token)
        if isinstance(user, TemplateResponse):
            return user, None

    try:
        student = Student.objects.get(student=user)
    except Student.DoesNotExist:
        return (
            response_403(
                req,
                msg=_(
                    "You must be a logged in student to access this "
                    "resource."
                ),
                logger_msg=(
                    "Student index page accessed by non-student account"
                ),
                log=logger.warning,
            ),
            None,
        )

    new_student = False
    if not user.is_active:
        user.is_active = True
        user.save()
        new_student = True

    logout(req)
    login(req, user, backend="peerinst.backends.CustomPermissionsBackend")

    return student, new_student


def get_context_data_index_page(req, student, new_student):

    token = create_student_token(
        student.student.username, student.student.email
    )

    StudentNotification.clean(student)

    groups = StudentGroupMembership.objects.filter(student=student)

    assignments = {
        group: [
            {
                "title": assignment.group_assignment.assignment.title,
                "pk": assignment.group_assignment.assignment.pk,
                "due_date": assignment.group_assignment.due_date,
                "link": "{}://{}{}".format(
                    req.scheme,
                    req.get_host(),
                    reverse(
                        "live",
                        kwargs={
                            "assignment_hash": assignment.group_assignment.hash,  # noqa
                            "token": token,
                        },
                    ),
                ),
                "results": assignment.results,
                "done": assignment.completed,
            }
            for assignment in StudentAssignment.objects.filter(
                student=student, group_assignment__group=group.group
            ).order_by("-group_assignment__due_date")
        ]
        for group in groups
    }

    assignments = {
        group: [
            {
                "title": assignment["title"],
                "pk": assignment["pk"],
                "due_date": assignment["due_date"],
                "link": assignment["link"],
                "results": assignment["results"],
                "done": assignment["done"],
            }
            for assignment in assignments
        ]
        for group, assignments in list(assignments.items())
    }

    latest_student_consent = (
        Consent.objects.filter(
            user__username=student.student.username, tos__role="student"
        )
        .order_by("-datetime")
        .first()
    )

    data = {
        "expiry_blinking_delay": 3,
        "new_student": new_student,
        "student": {
            "username": student.student.username,
            "email": student.student.email,
            "member_since": student.student.date_joined.isoformat(),
            "tos": {
                "sharing": latest_student_consent.accepted,
                "signed_on": latest_student_consent.datetime.isoformat(),
            },
        },
        "groups": [
            {
                "connected_course_url": None,
                "name": group.group.name,
                "teacher": [t.user.pk for t in group.group.teacher.all()],
                "title": group.group.title,
                "notifications": group.send_emails,
                "member_of": group.current_member,
                "assignments": [
                    {
                        "title": assignment["title"],
                        "pk": assignment["pk"],
                        "due_date": assignment["due_date"].isoformat(),
                        "link": assignment["link"],
                        "results": assignment["results"],
                        "done": assignment["done"],
                    }
                    for assignment in assignments[group]
                ],
                "student_id": group.student_school_id,
                "student_id_needed": group.group.student_id_needed,
            }
            for group in groups
        ],
        "notifications": [
            {
                "link": notification.link,
                "icon": notification.notification.icon,
                "text": gettext(notification.text),
                "pk": notification.pk,
            }
            for notification in student.notifications.order_by("-created_on")
        ],
        "urls": {
            "tos_modify": reverse(
                "tos:tos_modify", kwargs={"role": "student"}
            ),
            "remove_notification": reverse("student-remove-notification"),
            "remove_notifications": reverse("student-remove-notifications"),
            "join_group": reverse("student-join-group"),
            "leave_group": reverse("student-leave-group"),
            "save_student_id": reverse("student-change-id"),
            "student_toggle_group_notifications": reverse(
                "student-toggle-group-notifications"
            ),
        },
        "translations": {
            "assignment_about_to_expire": gettext(
                "This assignment is about to expire"
            ),
            "assignment_expired": gettext("Past due date"),
            "cancel": gettext("Cancel"),
            "course_flow_button": gettext("Visit this group's CourseFlow"),
            "completed": gettext("Completed"),
            "day": gettext("day"),
            "days": gettext("days"),
            "due_on": gettext("Due on"),
            "edit_student_id": gettext("Edit student id"),
            "expired": gettext("Expired"),
            "go_to_assignment": gettext("Go to assignment"),
            "grade": gettext("Grade"),
            "hour": gettext("hour"),
            "hours": gettext("hours"),
            "leave": gettext("Leave"),
            "leave_group_question": gettext("Are you sure?"),
            "leave_group_text": gettext(
                "This will remove you from the group. All your answers will "
                "be saved, but you won't appear as a member of the group to "
                "your teacher.  "
            ),
            "leave_group_title": gettext("Leave group"),
            "minute": gettext("minute"),
            "minutes": gettext("minutes"),
            "no_assignments": gettext("No assignments yet"),
            "notifications_bell": gettext(
                "Toggle email reminders for this group"
            ),
            "not_sharing": gettext("Not sharing"),
            "sharing": gettext("Sharing"),
            "student_id": gettext("Student id"),
            "student_id_needed": gettext(
                "You need to add your school's student id to do assignments "
                "for this group."
            ),
        },
    }

    return data


@require_safe
def index_page(req):
    """
    Main student page. Accessed through a link sent by email containing
    a token or without the token for a logged in student.
    """
    req.session["access_type"] = StudentGroup.STANDALONE

    token = req.GET.get("token")
    group_student_id_needed = req.GET.get("group-student-id-needed", "")

    student, new_student = login_student(req, token)
    if isinstance(student, HttpResponse):
        return student

    if not Consent.objects.filter(
        user=student.student, tos__role__role="student"
    ).exists():
        return HttpResponseRedirect(
            reverse("tos:tos_consent", kwargs={"role": "student"})
            + "?next="
            + req.path
        )

    data = get_context_data_index_page(req, student, new_student)

    context = {
        "data": json.dumps(data),
        "group_student_id_needed": group_student_id_needed,
        "access_standalone": True,
    }

    return render(req, "peerinst/student/index.html", context)


@login_required
@require_safe
def index_page_LTI(request):
    """
    Main student page when accessed via LTI for new accounts
    """
    course_id = request.session.get("context_id", None)

    if request.user.has_usable_password() or not course_id:
        # Only allow access via new LTI student accounts
        logout(request)
        return HttpResponseRedirect(reverse("lti-fail-auth"))

    user = request.user

    student, new_student = Student.objects.get_or_create(student=user)

    if not user.is_active or new_student:
        user.is_active = True
        user.save()
        new_student = True

    if not Consent.objects.filter(
        user=student.student, tos__role__role="student"
    ).exists():
        return HttpResponseRedirect(
            reverse("tos:tos_consent", kwargs={"role": "student"})
            + "?next="
            + request.path
        )

    manage_LTI_studentgroup(request)

    assignment_id = request.session.get("custom_assignment_id", None)
    question_id = request.session.get("custom_question_id", None)

    if assignment_id and question_id:
        request.session["access_type"] = StudentGroup.LTI
        logger.info(
            f"Session data for question view : {dict(request.session.items())}"
        )

        return HttpResponseRedirect(
            reverse(
                "question",
                kwargs={
                    "assignment_id": assignment_id,
                    "question_id": question_id,
                },
            ),
        )

    request.session["access_type"] = StudentGroup.LTI_STANDALONE
    logger.info(
        f"Session data for LTI standalone index : {dict(request.session.items())}"
    )

    data = get_context_data_index_page(request, student, new_student)

    context = {
        "data": json.dumps(data),
        "group_student_id_needed": "",
        "access_lti_standalone": True,
    }

    return render(request, "peerinst/student/index.html", context)


@student_required
@require_POST
def join_group(req, student):
    group = validate_group_data(req)
    if isinstance(group, HttpResponse):
        return group

    student.join_group(group, mail_type="new_group", request=req)

    try:
        membership = StudentGroupMembership.objects.get(
            student=student, group=group
        )
    except StudentGroupMembership.DoesNotExist:
        return response_400(
            req,
            msg=_("You don't seem to be part of this group."),
            logger_msg=(
                "Student {} isn't part of group {}.".format(
                    student.pk, group.pk
                )
            ),
            log=logger.warning,
        )

    token = create_student_token(
        student.student.username, student.student.email
    )

    data = {
        "name": group.name,
        "title": group.title,
        "notifications": membership.send_emails,
        "member_of": membership.current_member,
        "assignments": [
            {
                "title": assignment.group_assignment.assignment.title,
                "due_date": assignment.group_assignment.due_date.isoformat(),
                "link": "{}://{}{}".format(
                    req.scheme,
                    req.get_host(),
                    reverse(
                        "live",
                        kwargs={
                            "assignment_hash": assignment.group_assignment.hash,  # noqa
                            "token": token,
                        },
                    ),
                ),
                "results": assignment.results,
                "done": assignment.completed,
            }
            for assignment in StudentAssignment.objects.filter(
                student=student, group_assignment__group=group
            ).order_by("-group_assignment__due_date")
        ],
        "student_id": membership.student_school_id,
        "student_id_needed": group.student_id_needed,
    }

    return JsonResponse(data)


@student_required
@require_POST
def leave_group(req, student):
    group = validate_group_data(req)
    if isinstance(group, HttpResponse):
        return group

    student.leave_group(group)

    return HttpResponse()


@student_required
@require_POST
def toggle_group_notifications(req, student):
    group = validate_group_data(req)
    if isinstance(group, HttpResponse):
        return group

    membership = StudentGroupMembership.objects.get(
        student=student, group=group
    )

    notifications = not membership.send_emails

    membership.send_emails = notifications
    membership.save()

    return JsonResponse({"notifications": notifications})


@student_required
@require_POST
def remove_notification(req, student):
    """
    Removes the notification with the pk given as post value.

    Parameters
    ----------
    req : HttpRequest
        Request with post parameters:
            notification_pk : str
                Primary key of the notification
    student : Student
        Returned by @student_required (not used)

    Returns
    -------
    HttpResponse
        Empty 200 response if no errors or error response
    """
    try:
        data = json.loads(req.body)
    except ValueError:
        return response_400(
            req,
            msg=_("Wrong data type was sent."),
            logger_msg=("The sent data wasn't in a valid JSON format."),
            log=logger.warning,
        )

    try:
        notification_pk = data["notification_pk"]
    except KeyError as e:
        return response_400(
            req,
            msg=_("There are missing parameters."),
            logger_msg=("The arguments '%s' were missing.", ",".join(e.args)),
            log=logger.warning,
        )

    try:
        notification = StudentNotification.objects.get(pk=notification_pk)
    except StudentNotification.DoesNotExist:
        return HttpResponse()

    if notification.link == "":
        notification.delete()
        return HttpResponse()

    # if this is a notification with a link to an assignment
    assignment_hash = re.search(
        r"live/access/[0-9A-Za-z=_-]+/([0-9A-Za-z=_-]+)$", notification.link
    )
    if assignment_hash:
        group = StudentGroupAssignment.get(assignment_hash.group(1)).group
        if not group.student_id_needed:
            notification.delete()
            return HttpResponse()

        group_membership = StudentGroupMembership.objects.get(
            student=student, group=group
        )
        if group_membership.student_school_id == "":
            return HttpResponse(group.name)
        else:
            notification.delete()
            return HttpResponse()

    return HttpResponse()


@student_required
@require_POST
def remove_notifications(req, student):
    """
    Removes all notifications for the student.

    Parameters
    ----------
    req : HttpRequest
        Request
    student : Student
        Returned by @student_required

    Returns
    -------
    HttpResponse
        Empty 200 response if no errors or error response
    """
    StudentNotification.objects.filter(student=student).delete()

    return HttpResponse()


@student_required
@require_POST
def update_student_id(req, student):
    """
    Updates the student id.

    Parameters
    ----------
    req : HttpRequest
        Request with post parameters:
            student_id : str
                New student id
            group_name : str
                Name of the group (unique key)
    student : Student
        Student instance returned by @student_required

    Returns
    -------
    HttpResponse
        Empty 200 response if no errors or error response
    """
    try:
        data = json.loads(req.body)
    except ValueError:
        return response_400(
            req,
            msg=_("Wrong data type was sent."),
            logger_msg=("The sent data wasn't in a valid JSON format."),
            log=logger.warning,
        )

    try:
        student_id = data["student_id"]
        group_name = data["group_name"]
    except KeyError as e:
        return response_400(
            req,
            msg=_("There are missing parameters."),
            logger_msg=("The arguments '%s' were missing.", ",".join(e.args)),
            log=logger.warning,
        )

    try:
        group = StudentGroup.objects.get(name=group_name)
    except StudentGroup.DoesNotExist:
        return response_400(
            req,
            msg=_("The wanted group doesn't seem to exist."),
            logger_msg=(f"Group {group_name} doesn't exist."),
            log=logger.warning,
        )

    try:
        membership = StudentGroupMembership.objects.get(
            student=student, group=group
        )
    except StudentGroupMembership.DoesNotExist:
        return response_400(
            req,
            msg=_("You don't seem to be part of this group."),
            logger_msg=(
                "Student {} isn't part of group {}.".format(
                    student.pk, group.pk
                )
            ),
            log=logger.warning,
        )

    membership.student_school_id = student_id
    membership.save()
    logger.info(
        "Student id for student {} and group {} changed to {}.".format(
            student.pk, group.pk, student_id
        )
    )

    data = {"student_id": student_id}

    return JsonResponse(data)


@require_safe
def login_page(req):
    return render(req, "peerinst/student/login.html")


@require_POST
def send_signin_link(req):
    try:
        email = req.POST["email"].lower()
    except KeyError as e:
        return response_400(
            req,
            msg=_("There are missing parameters."),
            logger_msg=("The arguments '%s' were missing.", ",".join(e.args)),
            log=logger.warning,
        )

    student = Student.objects.filter(student__email=email).exclude(
        Q(
            password__startswith=UNUSABLE_PASSWORD_PREFIX
        )  # Exclude new LTI accounts
    )
    context = {}
    if not student:
        student, created = Student.get_or_create(email)
        if created:
            logger.info(f"Student created with email {email}.")
    elif len(student) == 1:
        student = student[0]
    else:
        username, __ = get_student_username_and_password(email)
        student = student.filter(student__username=username).first()
    if student:
        err = student.send_email(mail_type="signin", request=req)
        context["error"] = err is not None
    return render(req, "peerinst/student/login_confirmation.html", context)


@student_required
@require_safe
def get_notifications(req, student):
    """
    Returns the notification data for the current student.

    Parameters
    ----------
    req ; HttpRequest
        Request
    student : Student
        Student instance returned by @student_required

    Returns
    -------
    HttpResponse
        Empty 200 response if no errors or error response
    """
    data = {
        "notifications": [
            {
                "link": notification.link,
                "icon": notification.notification.icon,
                "text": gettext(notification.text),
                "pk": notification.pk,
            }
            for notification in student.notifications.order_by("-created_on")
        ],
        "urls": {
            "student_page": reverse("student-page"),
            "remove_notification": reverse("student-remove-notification"),
            "remove_notifications": reverse("student-remove-notifications"),
        },
    }
    return JsonResponse(data)


@student_required
@require_safe
def student_page(req, student):
    context = {}

    return render(req, "peerinst/student/page.html", context)
