# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from .teacher import Teacher


class RunningTask(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    description = models.TextField()
    teacher = models.ForeignKey(Teacher, related_name="running_tasks")
    datetime = models.DateTimeField(auto_now_add=True)
