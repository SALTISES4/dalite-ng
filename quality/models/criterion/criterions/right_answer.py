from django.db import models

from quality.models.quality_type import QualityType, QualityUseType

from ..criterion import Criterion, CriterionRules


class RightAnswerCriterion(Criterion):
    name = models.CharField(
        max_length=32, default="right_answer", editable=False
    )

    @staticmethod
    def info():
        return {
            "name": "right_answer",
            "full_name": "Right answer",
            "description": "Determines if the given answer is the correct "
            "one.",
        }

    @staticmethod
    def create_default():
        criterion = RightAnswerCriterion.objects.create(
            uses_rules=["only_last"]
        )
        criterion.for_quality_types.add(
            QualityType.objects.get(type="studentgroupassignment"),
            QualityType.objects.get(type="studentgroup"),
            QualityType.objects.get(type="teacher"),
            QualityType.objects.get(type="global"),
        )
        criterion.for_quality_use_types.add(
            QualityUseType.objects.get(type="evaluation")
        )
        criterion.save()
        return criterion

    def evaluate(self, answer, rules_pk):
        try:
            first_correct = answer.first_correct
            correct = answer.correct
        except AttributeError:
            raise ValueError("The Answer object is needed")

        rules = RightAnswerCriterionRules.objects.get(pk=rules_pk)

        if rules.only_last:
            quality = correct
        else:
            quality = 0.5 * (correct + first_correct)

        evaluation = {"version": self.version, "quality": float(quality)}
        evaluation.update(
            {criterion: val["value"] for criterion, val in rules}
        )
        return evaluation

    def batch_evaluate(self, answers, rules_pk):
        return [self.evaluate(answer, rules_pk) for answer in answers]


class RightAnswerCriterionRules(CriterionRules):
    only_last = models.BooleanField(
        verbose_name="Only last step evaluated",
        help_text=(
            "Only the second step (or first if no second step) is evaluated. "
            "If false, both steps are evaluated."
        ),
    )

    def __str__(self):
        return f"Rules {self.pk} for criterion right_answer"

    @staticmethod
    def get_or_create(threshold=1, only_last=False):
        """
        Creates or get the criterion rules.

        Parameters
        ----------
        threshold : float in [0, 1] (default : 0)
            Minimum value for the criterion to pass
        only_last : bool (default : False)
            If only the last step is evaluated

        Returns
        -------
        RightAnswerCriterionRules
            Instance

        Raises
        ------
        ValueError
            If the arguments have invalid values
        """
        if threshold < 0 or threshold > 1:
            raise ValueError("The threshold must be between 0 and 1")
        criterion, __ = RightAnswerCriterionRules.objects.get_or_create(
            threshold=threshold, only_last=only_last
        )
        return criterion
