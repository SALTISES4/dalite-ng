import logging

from django.http import HttpResponse, JsonResponse
from django.utils.translation import ugettext_lazy as translate
from django.views.decorators.http import require_GET, require_POST

from dalite.views.errors import response_400
from dalite.views.utils import get_json_params

from ..models import Question, QuestionFlag, QuestionFlagReason
from .decorators import ajax_login_required, teacher_required

logger = logging.getLogger("peerinst-views")


@require_GET
@ajax_login_required
@teacher_required
def get_flag_question_reasons(req, teacher):
    data = {"reasons": [q.title for q in QuestionFlagReason.objects.all()]}
    return JsonResponse(data)


@require_POST
@ajax_login_required
@teacher_required
def flag_question(req, teacher):
    args = get_json_params(req, args=["id", "reason"])
    if isinstance(args, HttpResponse):
        return args
    (question_id, reason), _ = args

    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return response_400(
            req,
            msg=translate("The question couldn't be found."),
            logger_msg=(
                "The question with pk {} couldn't be found.".format(
                    question_id
                )
            ),
            log=logger.warning,
        )

    try:
        flag_reason = QuestionFlagReason.objects.get(title=reason)
    except Question.DoesNotExist:
        return response_400(
            req,
            msg=translate("The flag reason couldn't be found."),
            logger_msg=(
                f"The question flag reason with title {reason} "
                + "couldn't be found."
            ),
            log=logger.warning,
        )

    flag = QuestionFlag.objects.create(
        question=question, user=teacher.user, flag=True
    )
    flag.flag_reason.add(flag_reason)
    logger.info("Question flagged!")

    return JsonResponse({})
