import logging

from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from dalite.views.errors import response_403
from peerinst.models import Student

logger = logging.getLogger("quality")


def logged_in_non_student_required(fct):
    def wrapper(req, *args, **kwargs):
        if (
            not isinstance(req.user, User)
            or Student.objects.filter(student=req.user).exists()
        ):
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(f"Access to {req.path} from student {req.user}."),
                log=logger.warning,
            )
        return fct(req, *args, **kwargs)

    return wrapper
