from django.contrib.contenttypes.models import ContentType

from models import TeacherNotification


class NotificationMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated():
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
