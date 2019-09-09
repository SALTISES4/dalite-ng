from __future__ import unicode_literals

import logging

from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from dalite.views.errors import response_400, response_403
from peerinst.models import (
    Student,
    StudentGroup,
    StudentGroupAssignment,
    Teacher,
)

logger = logging.getLogger("peerinst-views")


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
                logger_msg=(
                    "Access to {} with a non teacher user.".format(req.path)
                ),
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
                    msg=_(
                        'There is no group with hash "{}".'.format(group_hash)
                    ),
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
                **kwargs
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
                logger_msg=(
                    "Access to {} from a non teacher user.".format(req.path)
                ),
                log=logger.warning,
            )
        try:
            teacher = Teacher.objects.get(user=req.user)
            return fct(req, *args, teacher=teacher, **kwargs)
        except Teacher.DoesNotExist:
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(
                    "Access to {} from a non teacher user.".format(req.path)
                ),
                log=logger.warning,
            )

    return wrapper


def student_required(fct):
    def wrapper(req, *args, **kwargs):
        if not isinstance(req.user, User):
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(
                    "Access to {} from a non student user.".format(req.path)
                ),
                log=logger.warning,
            )
        try:
            student = Student.objects.get(student=req.user)
            return fct(req, *args, student=student, **kwargs)
        except Student.DoesNotExist:
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(
                    "Access to {} with a non student user.".format(req.path)
                ),
                log=logger.warning,
            )

    return wrapper
