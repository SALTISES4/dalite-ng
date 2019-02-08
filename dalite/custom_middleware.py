from django.template.response import TemplateResponse


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
