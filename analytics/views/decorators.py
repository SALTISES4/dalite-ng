import logging

from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from dalite.views.errors import response_403

logger = logging.getLogger("analytics")


def staff_required(fct):
    def wrapper(req, *args, **kwargs):
        if not isinstance(req.user, User):
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(f"Access to {req.path} from a non teacher user."),
                log=logger.warning,
            )
        if req.user.is_staff:
            return fct(req, *args, **kwargs)
        else:
            return response_403(
                req,
                msg=_("You don't have access to this resource."),
                logger_msg=(f"Access to {req.path} from a non teacher user."),
                log=logger.warning,
            )

    return wrapper
