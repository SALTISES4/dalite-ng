# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from reputation.logger import logger

from ..criterion import Criterion


class StudentRationaleEvaluationCriterion(Criterion):
    name = models.CharField(
        max_length=32, default="student_rationale_evaluation", editable=False
    )
    score_0 = models.IntegerField(default=-1)
    score_1 = models.IntegerField(default=0)
    score_2 = models.IntegerField(default=1)
    score_3 = models.IntegerField(default=1)

    def evaluate(self, student):
        """
        Evaluates the `student` using the evaluations given by teachers for
        their rationales. Score is calculated using the different scores in
        the model fields.

        Parameters
        ----------
        student : Student
            Student to evaluate

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
        super(StudentRationaleEvaluationCriterion, self).evaluate(student)
        scores = {0: -1, 1: 0, 2: 1, 3: 1}

        if student.__class__.__name__ == "Student":
            return (
                max(
                    0,
                    sum(
                        getattr(self, "score_{}".format(evaluation.score))
                        for answer in student.answers.all()
                        for evaluation in answer.answerannotation_set.all()
                    ),
                ),
                {},
            )
        else:
            msg = "`question` has to be of type Student."
            logger.error("TypeError: {}".format(msg))
            raise TypeError(msg)

    def info(self):
        return super(StudentRationaleEvaluationCriterion, self).info(
            {
                "name": "student_rationale_evaluation",
                "full_name": "Rationale evaluation",
                "description": "Gives a score representing the evaluation of "
                "rationales by teachers and researchers.",
            }
        )
