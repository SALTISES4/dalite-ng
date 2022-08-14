from cookie_consent.middleware import CleanCookiesMiddleware
from django.template.response import TemplateResponse
from django.utils.deprecation import MiddlewareMixin


def resp_405_middleware(get_response):
    def middleware(req):
        resp = get_response(req)
        if resp.status_code == 405:
            message = "Allowed methods: {allow}".format(allow=resp["Allow"])
            return TemplateResponse(
                req, "405.html", status=405, context={"message": message}
            ).render()
        else:
            return resp

    return middleware


def resp_503_middleware(get_response):
    def middleware(req):
        resp = get_response(req)
        if resp.status_code == 503:
            return TemplateResponse(req, "503.html", status=503).render()
        else:
            return resp

    return middleware


class CleanCookiesFixMiddleware(CleanCookiesMiddleware, MiddlewareMixin):
    # https://github.com/jazzband/django-cookie-consent/issues/13#issuecomment-1136968085
    pass
