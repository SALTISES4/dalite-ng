from __future__ import unicode_literals

from operator import itemgetter

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods

from ..forms import EmailChangeForm
from ..models import EmailConsent, EmailType, Role


@login_required
@require_http_methods(["GET"])
def email_consent_modify(req, role):
    username, role_ = _get_username_and_role(req, role)
    if isinstance(username, HttpResponse):
        return username

    email_types = _get_email_types(username, role_.role)

    form = EmailChangeForm()

    context = {
        "next": req.GET.get("next", "/welcome/"),
        "form": form,
        "username": username,
        "role": role,
        "email_types": email_types,
        "all_accepted": "all" not in list(map(itemgetter("type"), email_types))
        or next(e["accepted"] for e in email_types if e["type"] == "all"),
    }
    return render(req, "tos/email_modify.html", context)


@login_required
@require_http_methods(["POST"])
def email_consent_update(req, role):
    username, role_ = _get_username_and_role(req, role)
    if isinstance(username, HttpResponse):
        return username

    consents = [
        {
            "user": req.user,
            "email_type": email_type,
            "accepted": req.POST.get("{}-consent".format(email_type.type), "")
            == "on",
        }
        for email_type in EmailType.objects.filter(role=role_)
    ]

    for consent in consents:
        EmailConsent.objects.create(**consent)

    redirect_to = req.GET.get("next", "/welcome/")

    return HttpResponseRedirect(redirect_to)


@login_required
@require_http_methods(["POST"])
def change_user_email(req, role):
    username, role_ = _get_username_and_role(req, role)
    if isinstance(username, HttpResponse):
        return username

    form = EmailChangeForm(req.POST)
    if form.is_valid():
        req.user.email = form.cleaned_data["email"]
        req.user.save()
        redirect_to = req.GET.get("next", "/welcome/")
        return HttpResponseRedirect(redirect_to)

    email_types = _get_email_types(username, role_.role)

    context = {
        "form": form,
        "username": username,
        "role": role,
        "email_types": email_types,
        "all_accepted": "all" not in list(map(itemgetter("type"), email_types))
        or next(e["accepted"] for e in email_types if e["type"] == "all"),
    }

    return render(req, "tos/email_modify.html", context)


def _get_username_and_role(req, role):
    username = req.user.username

    if not User.objects.filter(username=username).exists():
        return (
            TemplateResponse(
                req,
                "400.html",
                context={
                    "message": _(
                        'The user "{}" doesn\'t exist.'.format(username)
                    )
                },
                status=400,
            ),
            None,
        )

    try:
        role_ = Role.objects.get(role=role)
    except Role.DoesNotExist:
        return (
            TemplateResponse(
                req,
                "400.html",
                context={
                    "message": _(
                        "The role {} doesn't seem to exist.".format(role)
                    )
                },
                status=400,
            ),
            None,
        )

    return username, role_


def _get_email_types(username, role):
    return [
        {
            "type": email_type.type,
            "title": email_type.title,
            "description": email_type.description,
            "accepted": EmailConsent.get(
                username, role, email_type.type, default=True, ignore_all=True
            ),
        }
        for email_type in EmailType.objects.filter(role=role).order_by(
            "show_order"
        )
    ]
