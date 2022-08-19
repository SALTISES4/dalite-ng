from cookie_consent.cache import all_cookie_groups
from cookie_consent.conf import settings
from cookie_consent.middleware import CleanCookiesMiddleware
from cookie_consent.models import ACTION_ACCEPTED, LogItem
from cookie_consent.util import (
    dict_to_cookie_str,
    get_cookie_dict_from_request,
    get_cookie_groups,
    is_cookie_consent_enabled,
)
from cookie_consent.views import CookieGroupAcceptView
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import smart_str

"""
This file contains patches for the django-cookie-consent package
- Fixes middleware bug
- Adds secure and samesite flags to cookies
"""


class CleanCookiesFixMiddleware(CleanCookiesMiddleware, MiddlewareMixin):
    # https://github.com/jazzband/django-cookie-consent/issues/13#issuecomment-1136968085

    def process_response(self, request, response):
        # https://github.com/jazzband/django-cookie-consent/blob/master/cookie_consent/middleware.py
        if not is_cookie_consent_enabled(request):
            return response
        cookie_dic = get_cookie_dict_from_request(request)
        for cookie_group in all_cookie_groups().values():
            if not cookie_group.is_deletable:
                continue
            group_version = cookie_dic.get(cookie_group.varname, None)
            for cookie in cookie_group.cookie_set.all():
                if cookie.name not in request.COOKIES:
                    continue
                if group_version == settings.COOKIE_CONSENT_DECLINE:
                    response.delete_cookie(
                        smart_str(cookie.name), cookie.path, cookie.domain
                    )
                if (
                    cookie_dic  # <-- Fixes error when missing
                    and group_version < cookie.get_version()
                    and not settings.COOKIE_CONSENT_OPT_OUT
                ):
                    response.delete_cookie(
                        smart_str(cookie.name), cookie.path, cookie.domain
                    )
        return response


def set_cookie_dict_to_response(response, dic):
    # https://github.com/jazzband/django-cookie-consent/pull/27
    COOKIE_SECURE = settings.SESSION_COOKIE_SECURE
    try:
        COOKIE_SAMESITE = settings.SESSION_COOKIE_SAMESITE
    except AttributeError:
        COOKIE_SAMESITE = "Lax"

    response.set_cookie(
        settings.COOKIE_CONSENT_NAME,
        dict_to_cookie_str(dic),
        settings.COOKIE_CONSENT_MAX_AGE,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )


def accept_cookies(request, response, varname=None):
    cookie_dic = get_cookie_dict_from_request(request)
    for cookie_group in get_cookie_groups(varname):
        cookie_dic[cookie_group.varname] = cookie_group.get_version()
        if settings.COOKIE_CONSENT_LOG_ENABLED:
            LogItem.objects.create(
                action=ACTION_ACCEPTED,
                cookiegroup=cookie_group,
                version=cookie_group.get_version(),
            )
    set_cookie_dict_to_response(response, cookie_dic)


class CookieGroupAcceptViewPatch(CookieGroupAcceptView):
    def process(self, request, response, varname):
        accept_cookies(request, response, varname)
