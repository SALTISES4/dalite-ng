from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import ReputationType


@receiver(post_migrate)
def add_reputation_types(sender, **kwargs):
    for quality_type in (
        ("question", "question"),
        ("assignment", "assignment"),
        ("teacher", "teacher"),
        ("student", "student"),
    ):
        type_, _ = ReputationType.objects.get_or_create(type=quality_type[0])
        if type_.model_name != quality_type[1]:
            type_.model_name = quality_type[1]
            type_.save()
