from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from ..models import Consent, Role, Tos


@login_required
@require_http_methods(["GET"])
def tos_consent(req, role, version=None):
    username = req.user.username
    _consent, context = _consent_view(req, username, role, version)
    if isinstance(_consent, HttpResponse):
        return _consent

    if _consent is None:
        return render(req, "tos/tos_modify.html", context)
    elif _consent:
        return JsonResponse({"consent": True})
    else:
        return JsonResponse({"consent": False})


@login_required
@require_http_methods(["GET"])
def tos_consent_modify(req, role, version=None):
    username = req.user.username
    _consent, context = _consent_view(req, username, role, version)
    if isinstance(_consent, HttpResponse):
        return _consent
    return render(req, "tos/tos_modify.html", context)


@login_required
@require_http_methods(["POST"])
def tos_consent_update(req, role, version):
    try:
        role_ = Role.objects.get(role=role.lower())
    except Role.DoesNotExist:
        return TemplateResponse(
            req,
            "400.html",
            context={"message": _(f"{role} isn't a valid role.")},
            status=400,
        )

    username = req.user.username

    try:
        accepted = req.POST["accepted"].lower() == "true"
    except KeyError:
        return TemplateResponse(
            req,
            "400.html",
            context={"message": _("There are missing parameters.")},
            status=400,
        )

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return TemplateResponse(
            req,
            "400.html",
            context={"message": _(f'The user "{username}" doesn\'t exist.')},
            status=400,
        )

    try:
        tos = Tos.objects.get(role=role_, version=version)
    except Tos.DoesNotExist:
        return TemplateResponse(
            req,
            "400.html",
            context={
                "message": _(
                    "There is no terms of service with version "
                    "{} for role {}".format(version, role)
                )
            },
            status=400,
        )

    Consent.objects.create(user=user, tos=tos, accepted=accepted)

    redirect_to = req.POST.get("redirect_to", "/welcome/")

    return HttpResponseRedirect(redirect_to)


def _consent_view(req, username, role, version):

    if not Role.objects.filter(role=role):
        return (
            TemplateResponse(
                req,
                "400.html",
                context={"message": _(f"{role} isn't a valid role.")},
                status=400,
            ),
            None,
        )
    if not User.objects.filter(username=username).exists():
        return (
            TemplateResponse(
                req,
                "400.html",
                context={
                    "message": _(f'The user "{username}" doesn\'t exist.')
                },
                status=400,
            ),
            None,
        )

    version = int(version) if version is not None else version

    if not Tos.objects.filter(role__role=role):
        return (
            TemplateResponse(
                req,
                "500.html",
                context={"message": _("There is no terms of service yet.")},
                status=500,
            ),
            None,
        )

    tos, err = Tos.get(role=role, version=version)

    if tos is None:
        return (
            TemplateResponse(
                req, "400.html", context={"message": _(err)}, status=400
            ),
            None,
        )

    consent_ = Consent.get(username=username, role=role, version=version)

    context = {
        "username": username,
        "role": role,
        "tos_text": tos.text,
        "version": tos.version,
        "current": tos.current,
        "redirect_to": req.GET.get("next", "/welcome/"),
    }

    return consent_, context


@login_required
def tos_required(req):
    return TemplateResponse(req, "tos/tos_required.html", status=403)
