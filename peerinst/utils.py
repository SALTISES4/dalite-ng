import base64
import math
from datetime import datetime, timedelta
from itertools import chain, islice

import jwt
import pytz
from django.conf import settings
from django.utils.translation import gettext_lazy as translate

DELTA = timedelta(weeks=16)


def create_token(payload, exp=DELTA):
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
        try:
            batch_iter = islice(source_iter, size)
            yield chain([next(batch_iter)], batch_iter)
        except StopIteration:
            break


def format_time(seconds):
    if seconds is None:
        return None

    days = math.trunc(seconds / 60 / 60 / 24)
    seconds = seconds - days * 60 * 60 * 24
    hours = math.trunc(seconds / 60 / 60)
    seconds = seconds - hours * 60 * 60
    minutes = math.trunc(seconds / 60)
    seconds = seconds - minutes * 60

    text = ""
    if days:
        text = f'{text}{days} {translate("day" if days == 1 else "days")}'
    if hours:
        text = f'{f"{text}, " if text else ""}{hours} {translate("hour" if hours == 1 else "hours")}'  # noqa E501

    if minutes:
        text = f'{f"{text}, " if text else ""}{minutes} {translate("minute" if minutes == 1 else "minutes")}'  # noqa E501

    if seconds:
        text = f'{f"{text}, " if text else ""}{seconds} {translate("second" if seconds == 1 else "seconds")}'  # noqa E501

    return text.strip()
