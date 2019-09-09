# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from reputation.logger import logger

from ..criterion import Criterion


class ConvincingRationalesCriterion(Criterion):
    name = models.CharField(
        max_length=32, default="convincing_rationales", editable=False
    )

    def evaluate(self, instance):
        """
        Evaluates the how how often a students rationales are chosen by others.

        Parameters
        ----------
        instance : student
            student whose rationales are evaluated

        Returns
        -------
        float
            Reputation as evaluated by the criterion

        Raises
        ------
        TypeError
            If `instance` isn't of type Student
        """
        super(ConvincingRationalesCriterion, self).evaluate(instance)
        if instance.__class__.__name__ == "Student":
            return (
                instance.answers_chosen_by_others.count(),
                {"times_shown": instance.answers_shown_to_others.count()},
            )
        else:
            msg = "`instance` has to be of type Student."
            logger.error("TypeError: {}".format(msg))
            raise TypeError(msg)

    def info(self):
        return super(ConvincingRationalesCriterion, self).info(
            {
                "name": "convincing_rationales",
                "full_name": "Writing convincing rationales",
                "description": "Number of times the rationales you "
                "wrote were chosen by other students as convincing.",
            }
        )
