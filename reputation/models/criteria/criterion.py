# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from itertools import chain

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as translate

from dalite.models.custom_fields import CommaSepField
from reputation.logger import logger

from ..reputation_type import ReputationType


def validate_list_floats_greater_0(val):
    for x in val:
        try:
            n = float(x)
        except ValueError:
            raise ValidationError(
                "The values must be comma separated floats greather or equal "
                "to 0."
            )
        if n < 0:
            raise ValidationError(
                "The values must be comma separated floats greather or equal "
                "to 0."
            )


class Criterion(models.Model):
    version = models.AutoField(primary_key=True)
    for_reputation_types = models.ManyToManyField(ReputationType)
    badge_thresholds = CommaSepField(
        distinct=True,
        blank=True,
        validators=[validate_list_floats_greater_0],
        help_text="Thresholds for the badges to be awarded.",
    )
    badge_colour = models.CharField(max_length=16, default="#0066ff")
    points_per_threshold = CommaSepField(
        default="[1]",
        verbose_name="Points per threshold",
        help_text="Number of reputation points for each criterion point up to "
        "the next threadhold, split by commas. This list should have the same "
        "length or have one more element than Thresholds.",
    )
    thresholds = CommaSepField(
        blank=True,
        default="",
        verbose_name="Thresholds",
        help_text="Thresholds for number of point change. If empty, all "
        "criterion points will give the same number of points. If one less "
        "than `Points per threshold`, the last point number goes to infinity. "
        "If it's the same length, the last number indicates the threshold "
        "after which points aren't gained.",
    )

    class Meta:
        abstract = True

    def __iter__(self):
        """
        Any attribute specific to the criterion version  should
        be added in the __iter__ method of the child model.
        You can use
        return itertools.chain(`child_iter`, Super(`Class`, self).__iter__())`
        to combine them.
        """
        return chain(
            self.info().iteritems(),
            {
                "version": self.version,
                "badge_thresholds": self.badge_thresholds,
                "badge_colour": self.badge_colour,
                "points_per_threshold": self.points_per_threshold,
                "thresholds": self.thresholds,
            }.iteritems(),
        )

    def __str__(self):
        return "{}: version {}".format(self.name, self.version)

    def evaluate(self, model):
        """
        Evaluates the reputation score of the given `model`. Classes inheriting
        must call the super method.

        Parameters
        ----------
        model : Model
            Model being evaluated. Must be in `for_reputation_types`

        Returns
        -------
        float
            Reputation as evaluated by the criterion

        Raises
        ------
        TypeError
            If the `model` isn't in the for_reputation_types
        """
        if not self.for_reputation_types.filter(
            type=model.__class__.__name__.lower()
        ):
            msg = "The criterion {} isn't available ".format(
                str(self)
            ) + "for reputation type {}.".format(
                model.__class__.__name__.lower()
            )
            logger.error(msg)
            raise TypeError(msg)

    def save(self, *args, **kwargs):
        """
        Saves the new criterion making sure the `name` field exists.
        """
        if not hasattr(self, "name"):
            raise NotImplementedError(
                "Your criterion needs to have a `name` field. Make sure it's "
                "different from the others or it may lead to some trouble "
                "down the line."
            )
        if len(self.points_per_threshold) != len(self.thresholds) and len(
            self.points_per_threshold
        ) - 1 != len(self.thresholds):
            raise ValidationError(
                translate(
                    "The length of `Points per threshold` must be the same "
                    "as `Thresholds` or one more."
                )
            )
        super(Criterion, self).save(*args, **kwargs)

    def info(self, info):
        point_description = " The points are awarded as "
        if not self.thresholds:
            point_description = (
                point_description
                + "{} for each of these.".format(self.points_per_threshold[0])
            )
        else:
            point_description = "{}{}".format(
                point_description,
                ", ".join(
                    "{} for each of these between {} and {}".format(
                        point, t0, t1
                    )
                    for point, t0, t1 in zip(
                        self.points_per_threshold,
                        [0] + self.thresholds[:-1],
                        self.thresholds,
                    )
                ),
            )
            if len(self.thresholds) == len(self.points_per_threshold):
                point_description = point_description + "."
            else:
                point_description = "{}{}.".format(
                    point_description,
                    ", and {} for each over {}".format(
                        self.points_per_threshold[-1], self.thresholds[-1]
                    ),
                )

        info["description"] = info["description"] + point_description

        return info
