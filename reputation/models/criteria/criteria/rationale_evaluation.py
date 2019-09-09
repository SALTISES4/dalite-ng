# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from reputation.logger import logger

from ..criterion import Criterion


class RationaleEvaluationCriterion(Criterion):
    name = models.CharField(
        max_length=32, default="rationale_evaluation", editable=False
    )

    def evaluate(self, teacher):
        """
        Evaluates the `teacher` using the number of rationale evaluations done.

        Parameters
        ----------
        teacher : Teacher
            Teacher to evaluate

        Returns
        -------
        float
            Reputation as evaluated by the criterion
        Dict[str, Any]
            Details about the calculation

        Raises
        ------
        TypeError
            If `instance` isn't of type Teacher
        """
        super(RationaleEvaluationCriterion, self).evaluate(teacher)
        if teacher.__class__.__name__ == "Teacher":
            return (
                teacher.user.answerannotation_set.filter(
                    score__isnull=False
                ).count(),
                {},
            )
        else:
            msg = "`question` has to be of type Teacher."
            logger.error("TypeError: {}".format(msg))
            raise TypeError(msg)

    def info(self):
        return super(RationaleEvaluationCriterion, self).info(
            {
                "name": "rationale_evaluation",
                "full_name": "Evaluation of rationales",
                "description": "Gives a score based on your evaluation of "
                "rationales.",
            }
        )
