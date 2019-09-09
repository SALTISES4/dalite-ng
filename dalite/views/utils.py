# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging

from django.utils.translation import ugettext_lazy as _

from dalite.views.errors import response_400

logger = logging.getLogger("reputation")


def get_json_params(req, args=[], opt_args=[]):
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
        args = [data[arg] for arg in args]
        opt_args = [data.get(arg) for arg in opt_args]
    except KeyError as e:
        return response_400(
            req,
            msg=_("There are missing parameters."),
            logger_msg=(
                "The arguments {} were missing.".format(", ".join(e.args))
            ),
            log=logger.warning,
        )
    return args, opt_args
