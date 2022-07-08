from django.http import HttpResponse, JsonResponse
from django.utils.translation import ugettext_lazy as _

from dalite.views.errors import response_400, response_403
from dalite.views.utils import get_json_params
from peerinst.models import Student

from ..logger import logger
from ..models import Reputation
from .decorators import student_required


@student_required
def student_reputation(req):
    args = get_json_params(req, args=["id"])
    if isinstance(args, HttpResponse):
        return args
    (student_id,), __ = args

    if req.user.student.pk != student_id:
        return response_403(
            req,
            msg=_("You don't have access to this resource."),
            logger_msg=(
                "Access to reputation of student {} from student {}.".format(
                    student_id, req.user.student.pk
                )
            ),
            log=logger.warning,
        )

    try:
        student = Student.objects.get(pk=student_id)
    except Student.DoesNotExist:
        return response_400(
            req,
            msg=_("This student doesn't exist."),
            logger_msg=(f"Tried to obtain student with pk {student_id}"),
            log=logger.warning,
        )

    if student.reputation is None:
        student.reputation = Reputation.create(student)
        student.save()

    reputation, reputations = student.reputation.evaluate()

    data = {"reputation": reputation, "reputations": reputations}
    return JsonResponse(data, status=200)
