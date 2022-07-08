from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from peerinst.models import (
    Answer,
    Collection,
    Discipline,
    Message,
    QuestionFlag,
    QuestionFlagReason,
    Subject,
)
from quality.models import NegWordsCriterionRules


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        staff_group, created = Group.objects.get_or_create(
            name="saltise_staff"
        )
        staff = User.objects.filter(is_staff=True)
        for staff_member in staff:
            staff_group.user_set.add(staff_member)
        content_types = []
        model_list = [
            Answer,
            Collection,
            Discipline,
            Message,
            QuestionFlag,
            Subject,
            QuestionFlagReason,
            NegWordsCriterionRules,
        ]
        for model in model_list:
            content_types.append(ContentType.objects.get_for_model(model))
        staff_permissions = Permission.objects.filter(
            content_type__in=content_types
        )
        for permission in staff_permissions:
            staff_group.permissions.add(permission)
        self.stdout.write("Permissions have been assigned.")
