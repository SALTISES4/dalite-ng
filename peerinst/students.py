import base64
import hashlib
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from .utils import create_token, verify_token

logger = logging.getLogger("peerinst-auth")


def create_student_token(username, email, exp=timedelta(weeks=16)):
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
        return (
            TemplateResponse(
                req,
                "400.html",
                context={
                    "message": _(
                        "This page isn't valid. You can try asking for a new "
                        "login link."
                    )
                },
                status=400,
            ),
            False,
        )

    try:
        user = User.objects.get(username=username)
        if not user.is_active:
            user.is_active = True
            user.save()
    except User.DoesNotExist:
        return (
            TemplateResponse(
                req,
                "400.html",
                context={
                    "message": _(
                        "There is no user corresponding to the given link. "
                        "You may try asking for another one."
                    )
                },
                status=400,
            ),
            False,
        )

    username_, password = get_student_username_and_password(email)

    if username == username_:
        user = authenticate(req, username=username, password=password)
        is_lti = False
    else:
        # to prevent errors from old invalid tokens
        try:
            passwords = get_lti_passwords(username)
        except UnboundLocalError:
            return (
                TemplateResponse(
                    req,
                    "400.html",
                    context={
                        "message": _(
                            "This page isn't valid. You can try asking for a "
                            "new login link."
                        )
                    },
                    status=400,
                ),
                False,
            )
        users_ = [
            authenticate(req, username=username, password=p) for p in passwords
        ]
        try:
            user = [u for u in users_ if u is not None][0]
        except IndexError:
            user = None

        is_lti = True

    if user is None:
        return (
            TemplateResponse(
                req,
                "400.html",
                context={
                    "message": _(
                        "There is no user corresponding to the given link. "
                        "You may try asking for another one."
                    )
                },
                status=400,
            ),
            False,
        )

    return user, is_lti


def get_student_username_and_password(email, max_username_length=30):
    key = settings.SECRET_KEY

    username = hashlib.md5(email.encode()).hexdigest()[:max_username_length]
    password = hashlib.md5((f"{username}:{key}").encode()).hexdigest()

    return username, password


def get_old_lti_student_username_and_password(user_id):
    """Copied from `dalite/__init__.py`"""
    try:
        binary_username = user_id.encode()
    except TypeError:
        username = user_id
    else:
        print(binary_username)
        username = (
            base64.urlsafe_b64encode(binary_username)
            .decode()
            .replace("=", "+")
        )

    password = hashlib.md5(
        (user_id + settings.PASSWORD_GENERATOR_NONCE).encode()
    ).digest()

    return username, password


def get_lti_passwords(hashed_username):
    key = settings.PASSWORD_GENERATOR_NONCE

    try:
        if hashed_username.endswith("++"):
            usernames = [
                base64.urlsafe_b64decode(hashed_username[:-2] + i + j).encode()
                for i in ("+", "=")
                for j in ("+", "=")
            ]
        elif hashed_username.endswith("+"):
            usernames = [
                base64.urlsafe_b64decode(hashed_username[:-1] + i).encode()
                for i in ("+", "=")
            ]
        else:
            usernames = [base64.urlsafe_b64decode(hashed_username).encode()]
    except TypeError:
        logger.error(
            "Error trying to encode hashed username %s.", hashed_username
        )

    passwords = [hashlib.md5(u + key).digest() for u in usernames]

    return passwords
