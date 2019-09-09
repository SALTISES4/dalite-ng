# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from dalite.views.errors import response_403

logger = logging.getLogger("reputation")


def logged_in_non_student_required(fct):
    def wrapper(req, *args, **kwargs):
        if not isinstance(req.user, User) or hasattr(req.user, "student"):
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(
                    "Access to {} from student {}.".format(req.path, req.user)
                ),
                log=logger.warning,
            )
        return fct(req, *args, **kwargs)

    return wrapper


def student_required(fct):
    def wrapper(req, *args, **kwargs):
        if not hasattr(req.user, "student"):
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(
                    "Access to {} with a non student user.".format(req.path)
                ),
                log=logger.warning,
            )

        return fct(req, *args, **kwargs)

    return wrapper
