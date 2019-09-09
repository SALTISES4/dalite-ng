# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64
from datetime import datetime, timedelta
from itertools import chain, islice

import jwt
import pytz
from django.conf import settings
from django.utils.translation import ugettext_lazy as translate


def create_token(payload, exp=timedelta(weeks=16)):
    key = settings.SECRET_KEY

    payload_ = payload.copy()
    payload_.update(
        {
            "aud": "dalite",
            "iat": datetime.now(pytz.utc),
            "exp": datetime.now(pytz.utc) + exp,
        }
    )

    return base64.urlsafe_b64encode(
        jwt.encode(payload_, key, algorithm="HS256").encode()
    ).decode()


def verify_token(token):
    key = settings.SECRET_KEY

    payload, err = None, None

    try:
        payload = jwt.decode(
            base64.urlsafe_b64decode(token.encode()).decode(),
            key,
            audience="dalite",
            algorithms="HS256",
        )
    except TypeError:
        err = "Invalid token"
    except KeyError:
        err = "Token was incorrectly created."
    except jwt.exceptions.ExpiredSignatureError:
        err = "Token expired"
    except jwt.InvalidTokenError:
        err = "Invalid token"

    return payload, err


def batch(iterable, size):
    source_iter = iter(iterable)
    while True:
        batch_iter = islice(source_iter, size)
        yield chain([batch_iter.next()], batch_iter)


def format_time(seconds):
    if seconds is None:
        return None

    days = seconds / 60 / 60 / 24
    seconds = seconds - days * 60 * 60 * 24
    hours = seconds / 60 / 60
    seconds = seconds - hours * 60 * 60
    minutes = seconds / 60
    seconds = seconds - minutes * 60

    text = ""
    if days:
        text = "{} {}".format(
            text, days, translate("day" if days == 1 else "days")
        )
    if hours:
        text = "{}{} {}".format(
            "{}, ".format(text) if text else "",
            hours,
            translate("hour" if hours == 1 else "hours"),
        )
    if minutes:
        text = "{}{} {}".format(
            "{}, ".format(text) if text else "",
            minutes,
            translate("minute" if minutes == 1 else "minutes"),
        )
    if seconds:
        text = "{}{} {}".format(
            "{}, ".format(text) if text else "",
            seconds,
            translate("second" if seconds == 1 else "seconds"),
        )

    return text.strip()
