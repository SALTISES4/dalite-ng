from django.db import models

from reputation.logger import logger

from ..criterion import Criterion


class QuestionLikedCriterion(Criterion):
    name = models.CharField(
        max_length=32, default="question_liked", editable=False
    )
    points_liked = models.IntegerField(default=1)
    points_used = models.IntegerField(default=2)

    @staticmethod
    def general_info():
        return {
            "name": "question_liked",
            "full_name": "Question popularity",
            "description": "Gives a score representing the number of times"
            " the questions you have made are liked and used by other"
            " teachers.",
        }

    def _evaluate_question(self, question, teacher=None):
        """
        Evaluates the `question` using the number of teachers having liked it
        and using it, excluding `teacher`.

        Parameters
        ----------
        question : Question
            Question to evaluate
        teacher : Optional[Teacher] (default : None)
            Teacher to ignore in evaluation

        Returns
        -------
        float
            Reputation as evaluated by the criterion
        Dict[str, Any]
            Details about the calculation
        """
        if teacher is None:
            return (
                (
                    question.favourite_questions.count() * self.points_liked
                    + sum(
                        1
                        for assignment in question.assignment_set.all()
                        if assignment.answer_set.filter(
                            question=question
                        ).exists()
                    )
                    * self.points_used
                ),
                {},
            )
        else:
            return (
                (
                    question.favourite_questions.exclude(
                        user_id=teacher.user.pk
                    ).count()
                    * self.points_liked
                    + sum(
                        1
                        for assignment in question.assignment_set.all()
                        if not assignment.owner.filter(
                            username=teacher.user.username
                        ).exists()
                        and assignment.answer_set.filter(
                            question=question
                        ).exists()
                    )
                    * self.points_used
                ),
                {},
            )

    def evaluate(self, instance):
        """
        Evaluates the `question` using the number of teachers having liked it
        and using it. If `instance` is a teacher, sums over all their
        questions.

        Parameters
        ----------
        instance : Question | Teacher
            Question or Teacher to evaluate

        Returns
        -------
        float
            Reputation as evaluated by the criterion
        Dict[str, Any]
            Details about the calculation

        Raises
        ------
        TypeError
            If `instance` isn't of type Question or Teacher
        """
        super().evaluate(instance)
        if instance.__class__.__name__ == "Question":
            return self._evaluate_question(instance)
        elif instance.__class__.__name__ == "Teacher":
            question_evaluations = [
                self._evaluate_question(question, instance)
                for question in instance.user.question_set.all()
            ]
            if not question_evaluations:
                return 0, {}
            return (
                sum(evaluation[0] for evaluation in question_evaluations),
                {
                    key: [
                        evaluation[1][key]
                        for evaluation in question_evaluations
                    ]
                    for key in list(question_evaluations[0][1].keys())
                },
            )
        else:
            msg = "`question` has to be of type Question."
            logger.error(f"TypeError: {msg}")
            raise TypeError(msg)

    def info(self):
        return super().info(QuestionLikedCriterion.general_info())
