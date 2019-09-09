# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from dalite.views.errors import response_400
from dalite.views.utils import get_json_params

from ..logger import logger
from .student import student_reputation
from .teacher import teacher_reputation


@login_required
@require_POST
def reputation(req):
    args = get_json_params(req, args=["reputation_type"])
    if isinstance(args, HttpResponse):
        return args
    (reputation_type,), __ = args

    if reputation_type == "teacher":
        return teacher_reputation(req)
    if reputation_type == "student":
        return student_reputation(req)
    else:
        return response_400(
            req,
            msg=_("This isn't a supported reputation type."),
            logger_msg=(
                "The sent data used reputation type {} ".format(
                    reputation_type
                )
                + "which isn't supported."
            ),
            log=logger.warning,
        )
