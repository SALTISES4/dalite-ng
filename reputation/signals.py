# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import ReputationType


@receiver(post_migrate)
def add_reputation_types(sender, **kwargs):
    for quality_type in ("question", "assignment", "teacher", "student"):
        ReputationType.objects.get_or_create(type=quality_type)
