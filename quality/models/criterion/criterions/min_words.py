from django.db import models
from django.utils.translation import gettext_lazy as _

from quality.models.quality_type import QualityType, QualityUseType

from ..criterion import Criterion, CriterionRules


class MinWordsCriterion(Criterion):
    name = models.CharField(max_length=32, default="min_words", editable=False)

    @staticmethod
    def info():
        return {
            "name": "min_words",
            "full_name": _("Depth"),
            "description": _(
                "Try going more in depth in explaining your " "reasoning."
            ),
        }

    @staticmethod
    def create_default():
        criterion = MinWordsCriterion.objects.create(uses_rules=["min_words"])
        criterion.for_quality_types.add(
            QualityType.objects.get(type="studentgroupassignment"),
            QualityType.objects.get(type="studentgroup"),
            QualityType.objects.get(type="teacher"),
            QualityType.objects.get(type="global"),
        )
        criterion.for_quality_use_types.add(
            QualityUseType.objects.get(type="validation"),
            QualityUseType.objects.get(type="evaluation"),
        )
        criterion.save()
        return criterion

    def evaluate(self, answer, rules_pk):
        if not isinstance(answer, str):
            answer = answer.rationale
        rules = MinWordsCriterionRules.objects.get(pk=rules_pk)
        evaluation = {
            "version": self.version,
            "quality": float(len(answer.split()) >= rules.min_words),
        }
        evaluation.update(
            {criterion: val["value"] for criterion, val in rules}
        )
        return evaluation

    def batch_evaluate(self, answers, rules_pk):
        rules = MinWordsCriterionRules.objects.get(pk=rules_pk)

        evaluations = [
            {
                "version": self.version,
                "quality": float(
                    len(
                        (
                            answer
                            if isinstance(answer, str)
                            else answer.rationale
                        ).split()
                    )
                    >= rules.min_words
                ),
            }
            for answer in answers
        ]

        for evaluation in evaluations:
            evaluation.update(
                {criterion: val["value"] for criterion, val in rules}
            )

        return evaluations


class MinWordsCriterionRules(CriterionRules):
    min_words = models.PositiveIntegerField(
        verbose_name="Min words",
        help_text="The minimum number of words needed by a rationale.",
    )

    def __str__(self):
        return f"Rules {self.pk} for criterion min_words"

    @staticmethod
    def get_or_create(threshold=1, min_words=0):
        """
        Creates or the criterion rules.

        Parameters
        ----------
        threshold : float in [0, 1] (default : 0)
            Minimum value for the criterion to pass
        min_words : int >= 0 (default : 0)
            Minimum number of words for the quality to evaluate to True.

        Returns
        -------
        MinWordsCriterionRules
            Instance

        Raises
        ------
        ValueError
            If the arguments have invalid values
        """
        if threshold < 0 or threshold > 1:
            raise ValueError("The threshold must be between 0 and 1")
        if min_words < 0:
            raise ValueError("The minmum number of words can't be negative.")
        criterion, __ = MinWordsCriterionRules.objects.get_or_create(
            threshold=threshold, min_words=min_words
        )
        return criterion
