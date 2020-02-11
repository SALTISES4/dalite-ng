import base64
import logging
from itertools import islice

from django.contrib.auth.tokens import default_token_generator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as translate
from django.views.decorators.http import require_POST, require_safe

from dalite.views.utils import with_json_params
from quality.models import RejectedAnswer, UsesCriterion, get_criterion

from ..models import NewUserRequest, Teacher
from ..tasks import send_mail_async

logger = logging.getLogger("peerinst-views")


@require_safe
def index(req):
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
                    ),
                    "token": default_token_generator.make_token(request.user),
                },
            ),
        )
        send_mail_async(
            translate("Please verify your myDalite account"),
            "Dear {},".format(request.user.username)
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
    context = {
        "criteria": [
            get_criterion(criterion)["criterion"].info()["full_name"]
            for criterion in set(
                UsesCriterion.objects.values_list("name", flat=True)
            )
        ]
    }
    return render(
        req, "peerinst/saltise_admin/flagged_rationales.html", context
    )


@require_POST
@with_json_params(opt_args=["idx", "n"])
def get_flagged_rationales(
    req: HttpRequest, idx: int = 0, n: int = 0
) -> HttpResponse:
    rationales = RejectedAnswer.objects.iterator()
    total = RejectedAnswer.objects.count()

    if n:
        if idx:
            rationales = [
                dict(rationale)
                for rationale in islice(rationales, idx, idx + n)
            ]
        else:
            rationales = [
                dict(rationale) for rationale in islice(rationales, n)
            ]
    else:
        if idx:
            rationales = [
                dict(rationale) for rationale in islice(rationales, idx, None)
            ]
        else:
            rationales = [dict(rationale) for rationale in rationales]

    data = {"rationales": rationales, "done": idx + len(rationales) == total}
    return JsonResponse(data)
