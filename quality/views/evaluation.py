import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from dalite.views.errors import response_400
from peerinst.models import Answer

from ..models import Quality

logger = logging.getLogger("quality")


@login_required
@require_POST
def evaluate_rationale(req):
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
        answer_pk = data["answer"]
        quality_pk = data["quality"]
    except KeyError as e:
        return response_400(
            req,
            msg=_("There are missing parameters."),
            logger_msg=(
                "The arguments {} were missing.".format(", ".join(e.args))
            ),
            log=logger.warning,
        )

    try:
        answer = Answer.objects.get(pk=answer_pk)
    except Answer.DoesNotExist:
        return response_400(
            req,
            msg=_("Some of the parameters were wrong."),
            logger_msg=(f"There isn't any answer with key {answer_pk}."),
            log=logger.warning,
        )

    try:
        quality = Quality.objects.get(pk=quality_pk)
        quality_, evaluation = quality.evaluate(answer)
        return JsonResponse({"quality": quality_, "evaluation": evaluation})
    except Quality.DoesNotExist:
        return response_400(
            req,
            msg=_("Some of the parameters were wrong."),
            logger_msg=(f"There isn't any quality with key {quality_pk}."),
            log=logger.warning,
        )
