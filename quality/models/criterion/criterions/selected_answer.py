# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from dalite.models.custom_fields import ProbabilityField
from quality.models.quality_type import QualityType, QualityUseType

from ..criterion import Criterion, CriterionRules


class SelectedAnswerCriterion(Criterion):
    name = models.CharField(
        max_length=32, default="selected_answer", editable=False
    )

    @staticmethod
    def info():
        return {
            "name": "selected_answer",
            "full_name": "Selected answer",
            "description": (
                "Scores based on number of times the rationale was selected."
            ),
        }

    @staticmethod
    def create_default():
        criterion = SelectedAnswerCriterion.objects.create(
            uses_rules=["default_if_never_shown"]
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
            shown = answer.shown_answer.filter(shown_answer=answer)
        except AttributeError:
            raise ValueError("The Answer object is needed")

        rules = SelectedAnswerCriterionRules.objects.get(pk=rules_pk)

        if not shown:
            quality = rules.default_if_never_shown
        else:
            quality = sum(
                a.shown_for_answer.chosen_rationale == answer for a in shown
            ) / len(shown)

        evaluation = {"version": self.version, "quality": quality}
        evaluation.update(
            {criterion: val["value"] for criterion, val in rules}
        )
        return evaluation

    def batch_evaluate(self, answers, rules_pk):
        return [self.evaluate(answer, rules_pk) for answer in answers]


class SelectedAnswerCriterionRules(CriterionRules):
    default_if_never_shown = ProbabilityField(
        verbose_name="Default value if never shown",
        help_text="Value to evaluate to if answer never shown before.",
    )

    def __str__(self):
        return "Rules {} for criterion selected_answer".format(self.pk)

    @staticmethod
    def get_or_create(threshold=1, default_if_never_shown=0):
        """
        Creates or get the criterion rules.

        Parameters
        ----------
        threshold : float in [0, 1] (default : 0)
            Minimum value for the criterion to pass
        default_if_never_shown : float in [0, 1] (default : 0)
            Value to show if answer never shown before

        Returns
        -------
        SelectedAnswerCriterionRules
            Instance

        Raises
        ------
        ValueError
            If the arguments have invalid values
        """
        if threshold < 0 or threshold > 1:
            raise ValueError("The threshold must be between 0 and 1")
        if default_if_never_shown < 0 or default_if_never_shown > 1:
            raise ValueError(
                "The default_if_never_shown must be between 0 and 1"
            )
        criterion, __ = SelectedAnswerCriterionRules.objects.get_or_create(
            threshold=threshold, default_if_never_shown=default_if_never_shown
        )
        return criterion
