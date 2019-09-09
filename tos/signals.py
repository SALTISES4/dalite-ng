from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import EmailType, Role


@receiver(post_migrate)
def row_addition_signal(sender, **kwargs):
    roles = ("teacher", "student")

    for role in roles:
        if not Role.objects.filter(role=role).exists():
            role_ = Role.objects.create(role=role)
            EmailType.objects.create(**all_email_type(role_))


def all_email_type(role):
    return {
        "role": role,
        "type": "all",
        "title": "All emails",
        "description": "Receive all emails from myDALITE",
    }
