from __future__ import unicode_literals

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    HttpResponseRedirect,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import render

from .forms import ConsentForm
from .models import Consent, Tos


@login_required
def consent(req, role, version=None):
    username = req.user.username
    _consent, context = _consent_view(req, username, role, version)
    if isinstance(_consent, HttpResponse):
        return _consent

    if _consent is None:
        return render(req, "tos/consent.html", context)
    elif _consent:
        return JsonResponse({"consent": True})
    else:
        return JsonResponse({"consent": False})


@login_required
def consent_modify(req, role, version=None):
    username = req.user.username
    _consent, context = _consent_view(req, username, role, version)
    if isinstance(_consent, HttpResponse):
        return _consent
    return render(req, "tos/consent.html", context)


@login_required
def consent_update(req, role, version):
    if req.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if role not in Tos.ROLES:
        return HttpResponseBadRequest("Not a valid role")

    username = req.user.username

    try:
        accepted = req.POST["accepted"].lower() == "true"
    except KeyError:
        return HttpResponseBadRequest("Missing parameters")

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponseBadRequest("User doesn't exist")

    try:
        tos = Tos.objects.get(role=role[:2], version=version)
    except Tos.DoesNotExist:
        return HttpResponseBadRequest(
            "There is no terms of service with version "
            '{} for role "{}"'.format(version, role)
        )

    Consent.objects.create(user=user, tos=tos, accepted=accepted)

    redirect_to = req.POST.get("redirect_to", "/welcome/")

    return HttpResponseRedirect(redirect_to)


def _consent_view(req, username, role, version):
    if req.method != "GET":
        return HttpResponseNotAllowed(["GET"]), None
    if role not in Tos.ROLES:
        return HttpResponseBadRequest("Not a valid role"), None
    if not User.objects.filter(username=username).exists():
        return HttpResponseBadRequest("User doesn't exist"), None

    version = int(version) if version is not None else version

    if not Tos.objects.filter(role=role[:2]):
        return (
            HttpResponseServerError(
                "There isn't any terms of service version yet."
            ),
            None,
        )

    tos, err = Tos.get(role=role, version=version)

    if tos is None:
        return HttpResponseBadRequest(err), None

    _consent = Consent.get(username=username, role=role, version=version)

    context = {
        "username": username,
        "role": role,
        "tos_text": tos.text,
        "version": tos.version,
        "current": tos.current,
        "redirect_to": req.GET.get("next", "/welcome/"),
    }

    return _consent, context
