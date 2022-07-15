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
                logger_msg=(f"Access to {req.path} from student {req.user}."),
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
                logger_msg=(f"Access to {req.path} with a non student user."),
                log=logger.warning,
            )

        return fct(req, *args, **kwargs)

    return wrapper
