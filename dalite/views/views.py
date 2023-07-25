from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView


def admin_index_wrapper(request):
    """
    Redirect to login page outside of an iframe, show help on enabling cookies
    inside an iframe.  We consider the request to come from within an iframe if
    the HTTP Referer header is set.  This isn't entirely accurate, but should
    be good enough.
    """
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("admin:index"))
    else:
        # We probably got here from within the Studio, and the user has
        # third-party cookies disabled, so we show help on enabling cookies for
        # this site.
        return render(
            request, "peerinst/cookie_help.html", {"host": request.get_host()}
        )


class StyleGuideView(TemplateView):
    """
    Render the styleguide app from Components
    """

    template_name = "styleguide.html"
