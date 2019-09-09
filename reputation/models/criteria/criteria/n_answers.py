# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from reputation.logger import logger

from ..criterion import Criterion


class NAnswersCriterion(Criterion):
    name = models.CharField(max_length=32, default="n_answers", editable=False)

    def evaluate(self, instance):
        """
        Evaluates the `questions` using the number of answers to it.

        Parameters
        ----------
        instance : Question | Student
            Question or Student to evaluate

        Returns
        -------
        float
            Reputation as evaluated by the criterion
        Dict[str, Any]
            Details about the calculation

        Raises
        ------
        TypeError
            If `instance` isn't of type Question or Student
        """
        super(NAnswersCriterion, self).evaluate(instance)
        if instance.__class__.__name__ == "Question":
            return instance.answer_set.count(), {}
        elif instance.__class__.__name__ == "Student":
            return instance.answers.count(), {}
        else:
            msg = "`question` has to be of type Question."
            logger.error("TypeError: {}".format(msg))
            raise TypeError(msg)

    def info(self):
        return super(NAnswersCriterion, self).info(
            {
                "name": "n_answers",
                "full_name": "Number of answers",
                "description": "Gives a score representing the number of "
                "answers.",
            }
        )
