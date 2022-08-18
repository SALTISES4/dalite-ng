import hashlib
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _

from .utils import create_token, verify_token

logger = logging.getLogger("peerinst-auth")
DELTA = timedelta(weeks=16)


def create_student_token(username, email, exp=DELTA):
    payload = {"username": username, "email": email}
    return create_token(payload, exp=exp)


def verify_student_token(token):
    payload, err = verify_token(token)
    if err is None:
        try:
            username = payload["username"]
            email = payload["email"]
        except KeyError:
            username = None
            email = None
            err = "This wasn't a student token"
    else:
        username, email = None, None

    return username, email, err


def authenticate_student(req, token):
    username, email, err = verify_student_token(token)

    if err is not None:
        return TemplateResponse(
            req,
            "400.html",
            context={"message": err},
            status=400,
        )

    try:
        user = User.objects.get(username=username)
        if not user.is_active:
            user.is_active = True
            user.save()
    except User.DoesNotExist:
        return TemplateResponse(
            req,
            "400.html",
            context={
                "message": _(
                    "There is no user corresponding to the given link. "
                    "You may try asking for another one."
                )
            },
            status=400,
        )

    username_, password = get_student_username_and_password(email)

    if username == username_:
        user = authenticate(req, username=username, password=password)

    if user is None:
        return TemplateResponse(
            req,
            "400.html",
            context={
                "message": _(
                    "There is no user corresponding to the given link. "
                    "You may try asking for another one."
                )
            },
            status=400,
        )

    return user


def get_student_username_and_password(email, max_username_length=30):
    key = settings.PWD_KEY

    username = hashlib.md5(email.encode()).hexdigest()[:max_username_length]
    password = hashlib.md5((f"{username}:{key}").encode()).hexdigest()

    return username, password
