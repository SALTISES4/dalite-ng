from django.db import models

from reputation.logger import logger

from ..criterion import Criterion


class CommonRationaleChoicesCriterion(Criterion):
    name = models.CharField(
        max_length=32, default="common_rationale_choices", editable=False
    )

    @staticmethod
    def general_info():
        return {
            "name": "common_rationale_choices",
            "full_name": "Choosing good rationales",
            "description": "Number of times the rationales you "
            "chose were also chosen by other students as convincing.",
        }

    def evaluate(self, instance):
        """
        Evaluates the how often a student chooses rationales that
        are are also chosen by others.

        Parameters
        ----------
        instance : student
            student whose rationale choices are evaluated

        Returns
        -------
        float
            Reputation as evaluated by the criterion

        Raises
        ------
        TypeError
            If `instance` isn't of type Student
        """
        super().evaluate(instance)
        if instance.__class__.__name__ == "Student":
            return (instance.answers_also_chosen_by_others.count(), {})
        else:
            msg = "`instance` has to be of type Student."
            logger.error(f"TypeError: {msg}")
            raise TypeError(msg)

    def info(self):
        return super().info(CommonRationaleChoicesCriterion.general_info())
