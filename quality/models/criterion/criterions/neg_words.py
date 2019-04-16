# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from quality.models.custom_fields import CommaSepField
from quality.models.quality_type import QualityType

from ..criterion import Criterion, CriterionRules


class NegWordsCriterion(Criterion):
    name = models.CharField(max_length=32, default="neg_words", editable=False)

    @staticmethod
    def info():
        return {
            "name": "neg_words",
            "full_name": "Negative words",
            "description": "Doesn't accept certain words.",
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

        return criterion

    def evaluate(self, answer, rules_pk):
        if not isinstance(answer, basestring):
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


class NegWordsCriterionRules(CriterionRules):
    neg_words = CommaSepField(
        distinct=True,
        verbose_name="Negative words",
        help_text="Words considered to be negative.",
        blank=True,
        null=True,
    )

    def __str__(self):
        return "Rules {} for criterion neg_words".format(self.pk)

    @staticmethod
    def get_or_create(threshold=1, neg_words=[]):
        """
        Creates or get the criterion rules.

        Parameters
        ----------
        threshold : float in [0, 1] (default : 0)
            Minimum value for the criterion to pass
        neg_words : str (default : "")
            Negative words split with a comma

        Returns
        -------
        NegWordsCriterionRules
            Instance

        Raises
        ------
        ValueError
            If the arguments have invalid values
        """
        if threshold < 0 or threshold > 1:
            raise ValueError("The threshold must be between 0 and 1")
        if not isinstance(neg_words, list):
            raise ValueError("The neg_words must be a list")
        criterion, __ = NegWordsCriterionRules.objects.get_or_create(
            threshold=threshold, neg_words=neg_words
        )
        return criterion
