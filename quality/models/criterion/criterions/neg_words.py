from django.db import models
from django.utils.translation import ugettext_lazy as _

from dalite.models.custom_fields import CommaSepField
from quality.models.quality_type import QualityType, QualityUseType

from ..criterion import Criterion, CriterionRules


class NegWordsCriterion(Criterion):
    name = models.CharField(max_length=32, default="neg_words", editable=False)

    @staticmethod
    def info():
        return {
            "name": "neg_words",
            "full_name": _("Toxicity"),
            "description": _("Please refrain from using toxic words."),
        }

    @staticmethod
    def create_default():
        criterion = NegWordsCriterion.objects.create(
            binary_threshold=True, uses_rules=["neg_words"]
        )
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

        return criterion

    def evaluate(self, answer, rules_pk):
        if not isinstance(answer, str):
            answer = answer.rationale
        rules = NegWordsCriterionRules.objects.get(pk=rules_pk)
        answer_words = answer.split()
        evaluation = {
            "version": self.version,
            "quality": 1
            - sum(
                1.0 for word in answer_words if word.lower() in rules.neg_words
            )
            / (len(answer_words) + 1e-16),
        }
        evaluation.update(
            {criterion: val["value"] for criterion, val in rules}
        )
        return evaluation

    def batch_evaluate(self, answers, rules_pk):
        rules = NegWordsCriterionRules.objects.get(pk=rules_pk)

        answers = [
            (answer if isinstance(answer, str) else answer.rationale).split()
            for answer in answers
        ]

        evaluations = [
            {
                "version": self.version,
                "quality": 1
                - sum(
                    1.0 for word in answer if word.lower() in rules.neg_words
                )
                / (len(answer) + 1e-16),
            }
            for answer in answers
        ]

        for evaluation in evaluations:
            evaluation.update(
                {criterion: val["value"] for criterion, val in rules}
            )

        return evaluations


class NegWordsCriterionRules(CriterionRules):
    neg_words = CommaSepField(
        distinct=True,
        verbose_name="Negative words",
        help_text="Words considered to be negative.",
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Rules {self.pk} for criterion neg_words"

    @staticmethod
    def get_or_create(threshold=1, neg_words=None):
        """
        Creates or get the criterion rules.

        Parameters
        ----------
        threshold : float in [0, 1] (default : 0)
            Minimum value for the criterion to pass
        neg_words : List[str] (default : [])
            Negative words

        Returns
        -------
        NegWordsCriterionRules
            Instance

        Raises
        ------
        ValueError
            If the arguments have invalid values
        """
        if neg_words is None:
            neg_words = []
        if threshold < 0 or threshold > 1:
            raise ValueError("The threshold must be between 0 and 1")
        if not isinstance(neg_words, list):
            raise ValueError("The neg_words must be a list")
        criterion, __ = NegWordsCriterionRules.objects.get_or_create(
            threshold=threshold, neg_words=neg_words
        )
        return criterion
