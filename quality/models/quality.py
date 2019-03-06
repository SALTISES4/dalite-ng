# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import models

from .criterion.criterion_list import criterions, get_criterion

logger = logging.getLogger("quality")


class Quality(models.Model):
    def evaluate(self, answer, *args, **kwargs):
        """
        Returns the quality as a tuple of the quality and the different
        criterion results.

        Returns
        -------
        Optional[float]
            Quality of the answer or None of no criterions present
        List[Dict[str, Any]]
            Individual criterions under the format
                [{
                    name: str
                    version: int
                    weight: int
                    quality: float
                }]
        """
        if not self.criterions.exists():
            return None, []

        criterions_ = [
            {
                "criterion": (
                    get_criterion(c.name).objects.latest()
                    if c.use_latest
                    else get_criterion(c.name).objects.get(version=c.version)
                ),
                "weight": c.weight,
            }
            for c in self.criterions.all()
        ]
        qualities = [
            {
                "name": c["criterion"].name,
                "version": c["criterion"].version,
                "weight": c["weight"],
                "quality": c["criterion"].evaluate(answer, *args, **kwargs),
            }
            for c in criterions_
        ]
        quality = float(
            sum(q["quality"] * q["weight"] for q in qualities)
        ) / sum(q["weight"] for q in qualities)
        return quality, qualities

    @staticmethod
    def available():
        return [criterion.info() for criterion in criterions.values()]


class UsesCriterion(models.Model):
    quality = models.ForeignKey(Quality, related_name="criterions")
    name = models.CharField(max_length=32)
    version = models.PositiveIntegerField()
    use_latest = models.BooleanField()
    weight = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        """
        Saves the new criterion making sure only one exists for each criterion
        `name` and the given `name` and version correspond to a criterion.

        Raises
        ------
        ValueError
            If either the `name` or `version` correspond to a non-existing
            criterion
        """
        criterion = get_criterion(self.name)
        if self.version >= criterion.objects.count():
            logger.error(
                "The criterion %s doesn't have a version %d.",
                self.name,
                self.version,
            )
            raise ValueError(
                "The used criterion has an invalid name or version."
            )
        UsesCriterion.objects.filter(
            quality=self.quality, name=self.name
        ).delete()
        super(UsesCriterion, self).save(*args, **kwargs)

    def __iter__(self):
        if self.use_latest:
            criterion = get_criterion(self.name).objects.latest()
        else:
            criterion = get_criterion(self.name).objects.get(
                version=self.version
            )
        data = {"use_latest": self.use_latest, "weight": self.weight}
        data.update(dict(criterion))
        return ((field, value) for field, value in data.items())
