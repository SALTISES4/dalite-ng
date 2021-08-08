from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import TeacherNotification


class NotificationMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                notification_type = ContentType.objects.get(
                    app_label="pinax_forums", model="ThreadSubscription"
                )
                request.session["forum_notifications"] = [
                    int(i)
                    for i in list(
                        TeacherNotification.objects.filter(
                            teacher=request.user.teacher
                        )
                        .filter(notification_type=notification_type)
                        .values_list("object_id", flat=True)
                    )
                ]
            except Exception:
                pass

        response = self.get_response(request)

        return response


class LTIAccessMiddleware:
    """
    If logged in via LTI, view must explicitly grant access, otherwise raise
    PermissionDenied
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        # LTI authentication hook sets LTI session key to True
        if request.session.get("LTI", False) and not getattr(
            view_func, "lti_access_allowed", False
        ):
            # If access is denied, force a logout to prevent being stuck
            return HttpResponseRedirect(reverse("access_denied_and_logout"))


def lti_access_allowed(view_func):
    """
    Modify a view function to allow access for an LTI login
    """

    view_func.lti_access_allowed = True

    return view_func
