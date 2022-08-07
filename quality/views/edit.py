import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST, require_safe

from dalite.views.errors import response_400, response_403
from peerinst.models import StudentGroup, StudentGroupAssignment, Teacher

from ..models import Quality, QualityType, QualityUseType, UsesCriterion
from ..utils import LazyEncoder
from .decorators import logged_in_non_student_required

logger = logging.getLogger("quality")


def verify_question(req, type_, question_pk):
    """
    Verifies if the question exists and the user is allowed to change the
    question, returning it if that's the case and an error response if not.

    Parameters
    ----------
    req : HttpRequest
        Request
    type_ : str
        Which use type it the quality for
    question_pk : int
        Primary key for the question

    Returns
    -------
    Either
        Quality
            Quality corresponding to the question
        HttpResponse
            400 or 403 error response
    """
    return response_400(
        req,
        msg=_("Some parameters are wrong"),
        logger_msg=(
            "An access to {} was tried with a question primary key.".format(
                req.path
            )
        ),
        log=logger.warning,
    )


def verify_assignment(req, type_, assignment_pk):
    """
    Verifies if the assignment exists and the user is allowed to change the
    assignment, returning it if that's the case and an error response if not.

    Parameters
    ----------
    req : HttpRequest
        Request
    type_ : str
        Which use type it the quality for
    assignment_pk : int
        Primary key for the assignment

    Returns
    -------
    Either
        Quality
            Quality corresponding to the assignment
        HttpResponse
            400 or 403 error response
    """
    try:
        assignment = StudentGroupAssignment.objects.get(pk=assignment_pk)
    except StudentGroupAssignment.DoesNotExist:
        return response_400(
            req,
            msg=_("Some parameters are wrong"),
            logger_msg=(
                f"An access to {req.path} was tried with the wrong "
                + f"assignment primary key {assignment_pk}."
            ),
            log=logger.warning,
        )

    try:
        teacher = Teacher.objects.get(user=req.user)
    except Teacher.DoesNotExist:
        return response_403(
            req,
            msg=_("You don't have access to this resource."),
            logger_msg=(f"Access to {req.path} from user {req.user.pk}."),
            log=logger.warning,
        )

    if not assignment.group.teacher.filter(pk=teacher.pk).exists():
        return response_403(
            req,
            msg=_("You don't have access to this resource."),
            logger_msg=(f"Access to {req.path} from user {req.user.pk}."),
            log=logger.warning,
        )

    if assignment.quality is None:
        quality_type = QualityType.objects.get(type="studentgroupassignment")
        try:
            quality_use_type = QualityUseType.objects.get(type=type_)
        except QualityUseType.DoesNotExist:
            return response_400(
                req,
                msg=_("Some parameters are wrong"),
                logger_msg=(
                    "An access to {} was tried with the wrong ".format(
                        req.path
                    )
                    + f"quality use type{type_}."
                ),
                log=logger.warning,
            )

        assignment.quality = Quality.objects.create(
            quality_type=quality_type, quality_use_type=quality_use_type
        )
        assignment.save()

    return assignment.quality


def verify_group(req, type_, group_pk):
    """
    Verifies if the group exists and the user is allowed to change the
    group, returning it if that's the case and an error response if not.

    Parameters
    ----------
    req : HttpRequest
        Request
    type_ : str
        Which use type it the quality for
    group_pk : int
        Primary key for the group

    Returns
    -------
    Either
        Quality
            Quality corresponding to the group
        HttpResponse
            400 or 403 error response
    """
    try:
        group = StudentGroup.objects.get(pk=group_pk)
    except StudentGroup.DoesNotExist:
        return response_400(
            req,
            msg=_("Some parameters are wrong"),
            logger_msg=(
                f"An access to {req.path} was tried with the wrong "
                + f"group primary key {group_pk}."
            ),
            log=logger.warning,
        )

    try:
        teacher = Teacher.objects.get(user=req.user)
    except Teacher.DoesNotExist:
        return response_403(
            req,
            msg=_("You don't have access to this resource."),
            logger_msg=(f"Access to {req.path} from user {req.user.pk}."),
            log=logger.warning,
        )

    if not group.teacher.filter(pk=teacher.pk).exists():
        return response_403(
            req,
            msg=_("You don't have access to this resource."),
            logger_msg=(f"Access to {req.path} from user {req.user.pk}."),
            log=logger.warning,
        )

    if group.quality is None:
        quality_type = QualityType.objects.get(type="studentgroup")
        try:
            quality_use_type = QualityUseType.objects.get(type=type_)
        except QualityUseType.DoesNotExist:
            return response_400(
                req,
                msg=_("Some parameters are wrong"),
                logger_msg=(
                    "An access to {} was tried with the wrong ".format(
                        req.path
                    )
                    + f"quality use type{type_}."
                ),
                log=logger.warning,
            )

        group.quality = Quality.objects.create(
            quality_type=quality_type, quality_use_type=quality_use_type
        )
        group.save()

    return group.quality


def verify_teacher(req, type_):
    """
    Verifies if the teacher exists , returning it if that's the case and an
    error response if not.

    Parameters
    ----------
    req : HttpRequest
        Request
    type_ : str
        Which use type it the quality for

    Returns
    -------
    Either
        Quality
            Quality corresponding to the group
        HttpResponse
            400 or 403 error response
    """
    try:
        teacher = Teacher.objects.get(user=req.user)
    except (Teacher.DoesNotExist, AttributeError):
        return response_403(
            req,
            msg=_("You don't have access to this resource."),
            logger_msg=(
                "Access to {} from user {}.".format(
                    req.path,
                    req.user.pk
                    if hasattr(req, "user") and isinstance(req.user, User)
                    else "anonymous",
                )
            ),
            log=logger.warning,
        )

    if teacher.quality is None:
        quality_type = QualityType.objects.get(type="teacher")
        try:
            quality_use_type = QualityUseType.objects.get(type=type_)
        except QualityUseType.DoesNotExist:
            return response_400(
                req,
                msg=_("Some parameters are wrong"),
                logger_msg=(
                    "An access to {} was tried with the wrong ".format(
                        req.path
                    )
                    + f"quality use type{type_}."
                ),
                log=logger.warning,
            )

        teacher.quality = Quality.objects.create(
            quality_type=quality_type, quality_use_type=quality_use_type
        )
        teacher.save()

    return teacher.quality


@logged_in_non_student_required
@require_safe
def index(req):
    """
    Returns the main page where it's possible to edit the quality.
    Possible query arguments are:
        assignment : int
            Primary key for a StudentGroupAssignment. If no Quality is
            associated with it, will be created
        next : str
            Page to return to once the edition is done. If not given, will go
            to /welcome
    If no query string is given, an error will be returned

    Returns
    -------
    HttpResponse
        Either a TemplateResponse for edition or an error response
    """
    try:
        type_ = req.GET["type"]
    except MultiValueDictKeyError:
        return response_400(
            req,
            msg=_("Some parameters are missing"),
            logger_msg=(
                f"An access to {req.path} was tried without a "
                + "primary key in the query string indicating what the "
                "quality is for."
            ),
            log=logger.error,
        )

    question_pk = req.GET.get("question")
    assignment_pk = req.GET.get("assignment")
    group_pk = req.GET.get("group")
    for_teacher = req.GET.get("teacher")
    next_ = req.GET.get("next")

    if question_pk is not None:
        quality = verify_question(req, type_, question_pk)
    elif assignment_pk is not None:
        quality = verify_assignment(req, type_, assignment_pk)
    elif group_pk is not None:
        quality = verify_group(req, type_, group_pk)
    elif for_teacher is not None:
        quality = verify_teacher(req, type_)
    else:
        return response_400(
            req,
            msg=_("Some parameters are missing"),
            logger_msg=(
                f"An access to {req.path} was tried without a "
                + "primary key in the query string indicating what the "
                "quality is for."
            ),
            log=logger.error,
        )

    if isinstance(quality, HttpResponse):
        return quality

    data = {
        "quality": dict(quality),
        "next": next_,
        "available": quality.available,
        "criterions": [
            dict(criterion) for criterion in quality.criterions.all()
        ],
        "urls": {
            "add_criterion": reverse("quality:add-criterion"),
            "update_criterion": reverse("quality:update-criterion"),
            "remove_criterion": reverse("quality:remove-criterion"),
        },
    }

    return render(
        req,
        "quality/edit/index.html",
        {"data": json.dumps(data, cls=LazyEncoder)},
    )


@login_required
@require_POST
def add_criterion(req):
    """
    Adds the given criterion to the quality with the given parameters. The
    request must have parameters:
        quality : int
            Primary key of the quality
        criterion : str
            Name of the criterion

    Returns
    -------
    HttpResponse
        Either a JsonResponse with the criterion data or an error response
    """
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
        quality_pk = data["quality"]
        criterion_name = data["criterion"]
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
        quality = Quality.objects.get(pk=quality_pk)
    except Quality.DoesNotExist:
        return response_400(
            req,
            msg=_("Some of the parameters were wrong."),
            logger_msg=(f"There isn't any quality with key {quality_pk}."),
            log=logger.warning,
        )

    try:
        criterion = quality.add_criterion(criterion_name)
    except ValueError:
        return response_400(
            req,
            msg=_("Some of the parameters were wrong."),
            logger_msg=(f"There isn't any quality with key {quality_pk}."),
            log=logger.warning,
        )

    logger.info(
        "Criterion %s was added to quality %d.", criterion_name, quality_pk
    )

    return JsonResponse(dict(criterion))


@login_required
@require_POST
def update_criterion(req):
    """
    Mofieds the criterion for the quality. The request must have parameters:
        quality : int
            Primary key of the quality
        criterion : str
            Name of the criterion
        field : str
            Name of the field to update
        value : Any
            New value for the field

    Returns
    -------
    HttpResponse
        Either a JsonResponse with the criterion data or an error response
    """
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
        quality_pk = data["quality"]
        criterion_name = data["criterion"]
        field = data["field"]
        value = data["value"]
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
        quality = Quality.objects.get(pk=quality_pk)
    except Quality.DoesNotExist:
        return response_400(
            req,
            msg=_("Some of the parameters were wrong."),
            logger_msg=(f"There isn't any quality with key {quality_pk}."),
            log=logger.warning,
        )

    try:
        criterion, old_value, value = quality.update_criterion(
            criterion_name, field, value
        )
    except (AttributeError, KeyError, UsesCriterion.DoesNotExist) as e:
        return response_400(
            req,
            msg=_("There was an error updating the criterion."),
            logger_msg=str(e),
            log=logger.warning,
        )

    logger.info(
        "Field %s for criterion %s in quality %d updated from %s to %s.",
        field,
        criterion_name,
        quality_pk,
        old_value,
        value,
    )

    return JsonResponse(dict(criterion))


@login_required
@require_POST
def remove_criterion(req):
    """
    REmoves the given criterion to the quality with the given parameters. The
    request must have parameters:
        quality : int
            Primary key of the quality
        criterion : str
            Name of the criterion

    Returns
    -------
    HttpResponse
        Either an empty HttpResponse or an error response
    """
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
        quality_pk = data["quality"]
        criterion_name = data["criterion"]
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
        quality = Quality.objects.get(pk=quality_pk)
    except Quality.DoesNotExist:
        return response_400(
            req,
            msg=_("Some of the parameters were wrong."),
            logger_msg=(f"There isn't any quality with key {quality_pk}."),
            log=logger.warning,
        )

    quality.remove_criterion(criterion_name)

    logger.info(
        "Criterion %s was removed from quality %d.", criterion_name, quality_pk
    )
    return HttpResponse()
