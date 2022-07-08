from django.db import models

from reputation.logger import logger

from ..criterion import Criterion


class StudentRationaleEvaluationCriterion(Criterion):
    name = models.CharField(
        max_length=32, default="student_rationale_evaluation", editable=False
    )
    points_score_0 = models.IntegerField(default=-1)
    points_score_1 = models.IntegerField(default=0)
    points_score_2 = models.IntegerField(default=1)
    points_score_3 = models.IntegerField(default=1)

    @staticmethod
    def general_info():
        return {
            "name": "student_rationale_evaluation",
            "full_name": "Rationale evaluation",
            "description": "Gives a score representing the evaluation of "
            "your rationales by teachers.",
        }

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
        super().evaluate(student)

        if student.__class__.__name__ == "Student":
            return (
                sum(
                    getattr(self, f"points_score_{evaluation.score}")
                    for answer in student.answers.all()
                    for evaluation in answer.answerannotation_set.filter(
                        score__isnull=False
                    ).all()
                ),
                {},
            )
        else:
            msg = "`question` has to be of type Student."
            logger.error(f"TypeError: {msg}")
            raise TypeError(msg)

    def info(self):
        return super().info(StudentRationaleEvaluationCriterion.general_info())
