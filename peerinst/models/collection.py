# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from .assignment import Assignment, StudentGroupAssignment
from .group import StudentGroup
from .question import Discipline
from .teacher import Teacher


class Collection(models.Model):
    assignments = models.ManyToManyField(Assignment, blank=True)
    discipline = models.ForeignKey(Discipline)
    owner = models.ForeignKey(Teacher, related_name="owner")
    followers = models.ManyToManyField(
        Teacher, blank=True, related_name="followers"
    )
    title = models.CharField(max_length=40)
    description = models.TextField(max_length=200)
    private = models.BooleanField(default=False)
    image = models.ImageField(
        _("Thumbnail image"),
        blank=True,
        null=True,
        upload_to="images",
        help_text=_(
            "Optional. An image to include in collection thumbnail. Accepted "
            "formats: .jpg, .jpeg, .png, .gif"
        ),
    )
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    last_modified = models.DateTimeField(auto_now=True, null=True)
    featured = models.BooleanField(default=False)

    def __unicode__(self):
        return self.title

    def make_studentgroupassignments(self, studentgroup_hash):
        """

        """
        group_obj = StudentGroup.get(studentgroup_hash)

        for a in self.assignments:
            (
                group_assignment,
                created,
            ) = StudentGroupAssignment.objects.get_or_create(
                group=group_obj, assignment=a
            )
        return

    def create_from_groupassignments():
        return
