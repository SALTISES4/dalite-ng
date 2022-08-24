import logging

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as translate
from django.views.decorators.http import require_safe

from dalite.views.errors import response_400
from dalite.views.utils import get_query_string_params
from peerinst.models import Teacher
from reputation.models import Reputation, UsesCriterion
from reputation.models.criterion_list import get_criterion

from .decorators import staff_required

logger = logging.getLogger("analytics")


@require_safe
@staff_required
def index(req):
    return render(req, "analytics/teachers/index.html")


@require_safe
@staff_required
def get_reputation_criteria_list(req):
    used_criteria = [
        criterion.name
        for criterion in UsesCriterion.objects.filter(
            reputation_type__type="teacher"
        )
    ]
    criteria = [
        get_criterion(criterion).general_info() for criterion in used_criteria
    ]
    data = {"criteria": criteria}
    return JsonResponse(data)


@require_safe
@staff_required
def get_teacher_list(req):
    data = {
        "teachers": [
            teacher.pk
            for teacher in Teacher.objects.order_by(
                "user__username"
            ).iterator()
        ]
    }
    return JsonResponse(data)


@require_safe
@staff_required
def get_teacher_information(req):
    args = get_query_string_params(req, args=["id"])
    if isinstance(args, HttpResponse):
        return args
    (id_,), _ = args

    try:
        teacher = Teacher.objects.get(pk=id_)
    except Teacher.DoesNotExist:
        return response_400(
            req,
            msg=translate("There is no teacher with that id"),
            logger_msg=(f"Teacher with pk {id_} couldn't be found."),
            log=logger.warning,
        )

    if teacher.reputation is None:
        teacher.reputation = Reputation.create(teacher)

    _, reputations = teacher.reputation.evaluate()

    data = {
        "username": teacher.user.username,
        "last_login": teacher.user.last_login.strftime("%Y-%m-%d %H:%M:%S")
        if teacher.user.last_login is not None
        else None,
        "reputations": [
            {
                "name": reputation["name"],
                "reputation": reputation["reputation"],
            }
            for reputation in reputations
        ],
    }
    return JsonResponse(data)
