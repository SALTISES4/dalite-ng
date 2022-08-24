import json
import logging
from operator import itemgetter

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from dalite.views.errors import response_400

from ..models import Quality, RejectedAnswer

logger = logging.getLogger("quality")


@login_required
@require_POST
def validate_rationale(req):
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
        rationale = data["rationale"]
        quality_pk = data.get("quality")
    except KeyError as e:
        return response_400(
            req,
            msg=_("There are missing parameters."),
            logger_msg=(
                "The arguments {} were missing.".format(", ".join(e.args))
            ),
            log=logger.warning,
        )

    global_quality = Quality.objects.get(
        quality_type__type="global", quality_use_type__type="validation"
    )

    global_quality_, global_evaluation = global_quality.evaluate(rationale)

    failed = [
        {"name": c["full_name"], "description": c["description"]}
        for c in global_evaluation
        if c["quality"]["quality"] < c["quality"]["threshold"]
        or (
            c["quality"]["quality"] < 1
            and c["versions"][c["version"] - 1]["binary_threshold"]
        )
    ]
    if failed:
        RejectedAnswer.add(global_quality, rationale, global_evaluation)

    if quality_pk is not None:
        try:
            quality = Quality.objects.get(pk=quality_pk)
            quality_, evaluation = quality.evaluate(rationale)
            failed = failed + [
                {"name": c["full_name"], "description": c["description"]}
                for c in evaluation
                if (
                    c["quality"]["quality"] < c["quality"]["threshold"]
                    or (
                        c["quality"]["quality"] < 1
                        and c["versions"][c["version"] - 1]["binary_threshold"]
                    )
                )
                and c["full_name"] not in list(map(itemgetter("name"), failed))
            ]
            if failed:
                RejectedAnswer.add(quality, rationale, evaluation)
        except Quality.DoesNotExist:
            return response_400(
                req,
                msg=_("Some of the parameters were wrong."),
                logger_msg=(f"There isn't any quality with key {quality_pk}."),
                log=logger.warning,
            )

    failed = {
        "error_msg": gettext(
            "That does not seem like a clear explanation of your reasoning:"
        ),
        "failed": failed,
    }
    return JsonResponse(failed)
