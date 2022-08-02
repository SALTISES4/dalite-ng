import base64
import logging

from django.contrib.admin import site
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.translation import gettext_lazy as translate
from django.views.decorators.http import require_POST, require_safe

from dalite.views.errors import response_400
from dalite.views.utils import with_json_params, with_query_string_params

from ..models import (
    AnswerAnnotation,
    Discipline,
    NewUserRequest,
    StudentGroup,
    Teacher,
)
from ..tasks import send_mail_async

logger = logging.getLogger("peerinst-views")


def index(req: HttpRequest) -> HttpResponse:
    if req.user.is_superuser:
        return site.index(req)
    else:
        return redirect(reverse("saltise-admin:index"))


@require_safe
def saltise_index(req: HttpRequest) -> HttpResponse:
    return render(req, "peerinst/saltise_admin/index.html")


@require_safe
def new_user_approval_page(req: HttpRequest) -> HttpResponse:
    context = {
        "new_users": [
            {
                "username": request.user.username,
                "date_joined": request.user.date_joined,
                "email": request.user.email,
                "url": request.user.url.url,
                "type": request.type.type,
            }
            for request in NewUserRequest.objects.order_by(
                "-user__date_joined"
            )
        ]
    }
    return render(
        req, "peerinst/saltise_admin/new_user_approval.html", context
    )


@require_POST
@with_json_params(args=["username", "approve"])
def verify_user(
    req: HttpRequest, username: str, approve: bool
) -> HttpResponse:
    request = NewUserRequest.objects.get(user__username=username)

    if approve:
        if request.type.type == "teacher":
            Teacher.objects.create(user=request.user)
        else:
            raise NotImplementedError(
                "The verification for user type {request.type.type} hasn't "
                "been implemented"
            )
        request.user.is_active = True
        request.user.save()

        link = "{}://{}{}".format(
            req.scheme,
            req.get_host(),
            reverse(
                "password_reset_confirm",
                kwargs={
                    "uidb64": base64.urlsafe_b64encode(
                        force_bytes(request.user.pk)
                    ).decode(),
                    "token": default_token_generator.make_token(request.user),
                },
            ),
        )
        send_mail_async(
            translate("Please verify your myDalite account"),
            f"Dear {request.user.username},"
            + "\n\nYour account has been recently activated. Please visit "
            "the following link to verify your email address and "
            "to set your password:\n\n"
            + link
            + "\n\nCheers,\nThe myDalite Team",
            "noreply@myDALITE.org",
            [request.user.email],
            fail_silently=True,
            html_message=loader.render_to_string(
                "registration/verification_email.html",
                context={"username": request.user.username, "link": link},
                request=req,
            ),
        )

        request.delete()

        logger.info(f"New user {username} approved")

    else:
        request.user.delete()
        logger.info(f"New user {username} refused")

    return HttpResponse("")


@require_safe
def flagged_rationales_page(req: HttpRequest) -> HttpResponse:
    return render(req, "peerinst/saltise_admin/flagged_rationales.html")


@require_safe
def get_flagged_rationales(req: HttpRequest) -> HttpResponse:
    data = {
        "rationales": [
            {
                "rationale": a.answer.rationale,
                "annotator": a.annotator.username,
                "timestamp": a.timestamp,
                "note": a.note,
                "answer_pk": a.answer.pk,
            }
            for a in AnswerAnnotation.objects.filter(
                score=0, answer__show_to_others=True
            )
        ]
    }
    return JsonResponse(data)


@require_safe
@with_query_string_params(args=["discipline"])
def get_groups_activity(req: HttpRequest, discipline: str) -> HttpResponse:
    try:
        discipline = Discipline.objects.get(title=discipline)
    except Discipline.DoesNotExist:
        return response_400(
            req,
            f"There is no discipline {discipline}.",
            "A request to get group activity for non existing "
            f"discipline {discipline} was made.",
            logger.warning,
            use_template=False,
        )

    groups = [
        group
        for group in StudentGroup.objects.iterator()
        if group.teacher.count()
        and discipline in group.teacher.first().disciplines.all()
    ]

    data = {
        "activity": [
            {
                "name": group.title,
                "teacher": group.teacher.last().user.username,
                "n_students": group.studentgroupmembership_set.count(),
                "semester": group.semester,
                "year": group.year,
            }
            for group in groups
        ]
    }

    return JsonResponse(data)
