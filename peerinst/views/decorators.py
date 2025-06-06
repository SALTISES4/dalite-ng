import logging
from functools import wraps

from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from dalite.views.errors import response_400, response_403
from peerinst.models import (
    Student,
    StudentGroup,
    StudentGroupAssignment,
    Teacher,
)

logger = logging.getLogger("peerinst-views")


def ajax_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        response = JsonResponse({"login_url": settings.LOGIN_URL})
        response.status_code = 401
        return response

    return _wrapped_view


def ajax_user_passes_test(test_func):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            response = JsonResponse({"message": "Forbidden"})
            response.status_code = 403
            return response

        return _wrapped_view

    return decorator


def group_access_required(fct):
    def wrapper(req, *args, **kwargs):
        group_hash = kwargs.get("group_hash", None)
        assignment_hash = kwargs.get("assignment_hash", None)
        return_assignment = assignment_hash is not None

        if group_hash is None and assignment_hash is None:
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(
                    "Access to {} without a group or assignment hash.".format(
                        req.path
                    )
                ),
                log=logger.warning,
            )

        try:
            teacher = Teacher.objects.get(user=req.user)
        except Teacher.DoesNotExist:
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(f"Access to {req.path} with a non teacher user."),
                log=logger.warning,
            )

        if assignment_hash is not None:
            assignment = StudentGroupAssignment.get(assignment_hash)
            if assignment is None:
                return response_400(
                    req,
                    msg=_(
                        'There is no assignment with hash "{}".'.format(
                            assignment_hash
                        )
                    ),
                    logger_msg=(
                        "Access to {} with a invalid assignment hash.".format(
                            req.path
                        )
                    ),
                    log=logger.warning,
                )
            group = assignment.group
        else:
            group = StudentGroup.get(group_hash)
            if group is None:
                return response_400(
                    req,
                    msg=_(f'There is no group with hash "{group_hash}".'),
                    logger_msg=(
                        "Access to {} with a invalid group hash.".format(
                            req.path
                        )
                    ),
                    log=logger.warning,
                )

        if teacher not in group.teacher.all():
            return response_403(
                req,
                msg=_(
                    "You don't have access to this resource. You must be "
                    "registered as a teacher for the group {}.".format(
                        group.name
                    )
                ),
                logger_msg=(
                    "Invalid access to group {} from teacher {}.".format(
                        group.pk, teacher.pk
                    )
                ),
                log=logger.warning,
            )

        if return_assignment:
            return fct(
                req,
                *args,
                teacher=teacher,
                group=group,
                assignment=assignment,
                **kwargs,
            )
        else:
            return fct(req, *args, teacher=teacher, group=group, **kwargs)

    return wrapper


def teacher_required(fct):
    def wrapper(req, *args, **kwargs):
        if not isinstance(req.user, User):
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(f"Access to {req.path} from a non teacher user."),
                log=logger.warning,
            )
        try:
            teacher = Teacher.objects.get(user=req.user)
            return fct(req, *args, teacher=teacher, **kwargs)
        except Teacher.DoesNotExist:
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(f"Access to {req.path} from a non teacher user."),
                log=logger.warning,
            )

    return wrapper


def student_required(fct):
    def wrapper(req, *args, **kwargs):
        if not isinstance(req.user, User):
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(f"Access to {req.path} from a non student user."),
                log=logger.warning,
            )
        try:
            student = Student.objects.get(student=req.user)
            return fct(req, *args, student=student, **kwargs)
        except Student.DoesNotExist:
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(f"Access to {req.path} with a non student user."),
                log=logger.warning,
            )

    return wrapper
