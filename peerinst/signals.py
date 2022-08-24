from django.contrib.auth.signals import user_logged_out
from django.core.exceptions import ObjectDoesNotExist
from django.core.signals import request_started
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone

from .models import LastLogout, MessageType, StudentNotificationType, UserType


@receiver(request_started)
def logger_signal(sender, environ=None, scope=None, **kwargs):
    # TODO: Update logger to operate in wsgi or asgi modes

    if environ and "HTTP_USER_AGENT" in environ:
        log = {"HTTP_REFERER": environ.get("HTTP_REFERER")}
        log["HTTP_USER_AGENT"] = environ.get("HTTP_USER_AGENT")
        log["REMOTE_ADDR"] = environ.get("REMOTE_ADDR")
        log["QUERY_STRING"] = environ.get("QUERY_STRING")
        log["timestamp"] = str(timezone.now())


@receiver(post_migrate)
def init_student_notification_types(sender, **kwargs):
    notifications = [
        {"type": "new_assignment", "icon": "assignment"},
        {"type": "assignment_about_to_expire", "icon": "assignment_late"},
        {"type": "assignment_due_date_changed", "icon": "schedule"},
    ]
    for notification in notifications:
        if not StudentNotificationType.objects.filter(
            type=notification["type"]
        ).exists():
            StudentNotificationType.objects.create(**notification)


@receiver(user_logged_out)
def update_last_logout(sender, request, user, **kwargs):
    if user and user.is_authenticated:
        try:
            last_logout = LastLogout.objects.get(user=user)
            last_logout.save()
        except ObjectDoesNotExist:
            last_logout = LastLogout.objects.create(user=user)


@receiver(post_migrate)
def init_message_types(sender, **kwargs):
    types = [
        {"type": "new_user", "removable": True, "colour": "#6600ff"},
        {
            "type": "saltise_annoncement",
            "removable": False,
            "colour": "#eaf7fb",
        },
        {"type": "dalite_annoncement", "removable": True, "colour": "#54c0db"},
    ]
    for type_ in types:
        if not MessageType.objects.filter(type=type_["type"]).exists():
            MessageType.objects.create(**type_)


@receiver(post_migrate)
def init_user_types(sender, **kwargs):
    types = [
        {"type": "teacher"},
        {"type": "researcher"},
    ]
    for type_ in types:
        if not UserType.objects.filter(type=type_["type"]).exists():
            UserType.objects.create(**type_)
