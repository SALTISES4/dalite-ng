# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from reputation.logger import logger

from ..criterion import Criterion


class NQuestionsCriterion(Criterion):
    name = models.CharField(
        max_length=32, default="n_questions", editable=False
    )

    def evaluate(self, teacher):
        """
        Evaluates the `teacher` using the number of questions composed.

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
            If `teacher` isn't of type Teacher
        """
        super(NQuestionsCriterion, self).evaluate(teacher)
        if teacher.__class__.__name__ != "Teacher":
            msg = "`teacher` has to be of type Teacher."
            logger.error("TypeError: {}".format(msg))
            raise TypeError(msg)

        return teacher.user.question_set.count(), {}

    def info(self):
        return super(NQuestionsCriterion, self).info(
            {
                "name": "n_questions",
                "full_name": "Number of questions",
                "description": "Gives a score representing the number of "
                "questions.",
            }
        )
