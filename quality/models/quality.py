import hashlib
import json
import logging
from itertools import chain

from django.db import models

from .criterion.criterion_list import criterions, get_criterion
from .quality_type import QualityType, QualityUseType

logger = logging.getLogger("quality")


class Quality(models.Model):
    quality_type = models.ForeignKey(QualityType, on_delete=models.CASCADE)
    quality_use_type = models.ForeignKey(
        QualityUseType, on_delete=models.CASCADE
    )

    def __str__(self):
        if self.quality_type.type == "global":
            return "{} for {} and use type {}".format(
                self.pk, self.quality_type, self.quality_use_type
            )
        else:
            return "{} for {}: {} and use type {}".format(
                self.pk,
                self.quality_type,
                str(getattr(self, f"{self.quality_type.type}_set").first()),
                self.quality_use_type,
            )

    def __iter__(self):
        return chain(
            iter(
                {
                    "pk": self.pk,
                    "quality_type": self.quality_type.type,
                    "quality_use_type": self.quality_use_type.type,
                }.items()
            ),
            *(
                iter(dict(criterion).items())
                for criterion in self.criterions.all()
            ),
        )

    def evaluate(self, answer, cache=False):
        """
        Returns the quality as a tuple of the quality and the different
        criterion results.

        Parameters
        ----------
        answer : Union[Answer, str]
            Answer to evaluate

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
                    threshold: float
                }]
        """
        if not self.criterions.exists():
            return None, []

        criterions_ = [
            {
                "criterion": (
                    get_criterion(c.name)["criterion"].objects.get(
                        version=c.version
                    )
                ),
                "rules": c.rules,
                "weight": c.weight,
            }
            for c in self.criterions.all()
        ]

        if cache:
            quality, qualities = QualityCache.get(self, answer)

        if not cache or quality is None:
            qualities = [
                dict(
                    chain(
                        iter(dict(c["criterion"]).items()),
                        iter(
                            {
                                "weight": c["weight"],
                                "quality": c["criterion"].evaluate(
                                    answer, c["rules"]
                                ),
                            }.items()
                        ),
                    )
                )
                for c in criterions_
            ]
            quality = float(
                sum(q["quality"]["quality"] * q["weight"] for q in qualities)
            ) / sum(q["weight"] for q in qualities)

            if cache:
                QualityCache.cache(self, answer, quality, qualities)

        return quality, qualities

    def batch_evaluate(self, answers, cache=False):
        if not self.criterions.exists():
            return [(None, [])]

        answers = list(answers)

        criterions_ = [
            {
                "criterion": (
                    get_criterion(c.name)["criterion"].objects.get(
                        version=c.version
                    )
                ),
                "rules": c.rules,
                "weight": c.weight,
            }
            for c in self.criterions.all()
        ]

        if cache:
            cached = [QualityCache.get(self, answer) for answer in answers]
            answers = [a for a, c in zip(answers, cached) if c[0] is None]
        else:
            cached = [(None, None) for _ in answers]

        qualities = [
            c["criterion"].batch_evaluate(answers, c["rules"])
            for c in criterions_
        ]
        qualities = [
            [
                dict(
                    chain(
                        iter(dict(c["criterion"]).items()),
                        iter({"weight": c["weight"], "quality": q}.items()),
                    )
                )
                for c, q in zip(criterions_, quality)
            ]
            for quality in zip(*qualities)
        ]

        quality = [
            float(
                sum(q["quality"]["quality"] * q["weight"] for q in _qualities)
            )
            / sum(q["weight"] for q in _qualities)
            for _qualities in qualities
        ]

        combined = [(q, qq) for q, qq in zip(quality, qualities)]

        if cache:
            for (q, qq), answer in zip(combined, answers):
                QualityCache.cache(self, answer, q, qq)

            gen = iter(combined)
            combined = [q if q[0] is not None else next(gen) for q in cached]

        return combined

    def add_criterion(self, name):
        """
        Adds the given criterion with latest version and default rules to the
        quality.

        Parameters
        ----------
        name : str
            Name of the criterion

        Returns
        -------
        UsesCriterion
            Created criterion

        Raises
        ------
        ValueError
            If the given criterion doesn't exist or isn't available for this
            quality type
        """
        if name not in [c["name"] for c in self.available]:
            msg = "The criterion {} isn't available for quality {}.".format(
                name, self.pk
            )
            logger.error(msg)
            raise ValueError(msg)

        criterion_class = get_criterion(name)

        version = (
            criterion_class["criterion"]
            .objects.filter(for_quality_types=self.quality_type)
            .last()
            .version
        )

        rules = criterion_class["rules"].get_or_create()

        return UsesCriterion.objects.create(
            quality=self, name=name, version=version, rules=rules.pk, weight=1
        )

    def update_criterion(self, name, field, value):
        """
        Modifies the given criterion field with value.

        Parameters
        ----------
        name : str
            Name of the criterion
        field : str
            Field to modify
        value : Any
            New value

        Returns
        -------
        UsesCriterion
            Updated criterion
        Any
            Previous value of the field

        Raises
        ------
        AttributeError
            If the given field doesn't exist
        UsesCriterion.DoesNotExist
            If there is no used criterio with the given name
        """
        try:
            criterion = UsesCriterion.objects.get(quality=self, name=name)
        except UsesCriterion.DoesNotExist:
            raise UsesCriterion.DoesNotExist(
                f"There is no criterion with name {name}."
            )

        if field in ("version", "weight"):
            old_value = getattr(criterion, field)
            setattr(criterion, field, value)
            criterion.save()
        else:
            rules = get_criterion(name)["rules"].objects.get(
                pk=criterion.rules
            )
            type_ = dict(rules)[field]["type"]
            if type_ == "ManyToManyField":
                old_value = list(map(str, getattr(rules, field).all()))
                if value:
                    getattr(rules, field).add(value)
                    value = old_value + [value]
                else:
                    getattr(rules, field).remove(old_value[-1])
                    value = old_value[:-1]
                rules.save()
            else:
                old_value = getattr(rules, field)
                if type_ == "CommaSepField":
                    if value:
                        value = old_value + [value]
                    else:
                        value = old_value[:-1]
                setattr(rules, field, value)
            rules.save()

        return criterion, old_value, value

    def remove_criterion(self, name):
        UsesCriterion.objects.filter(quality=self, name=name).delete()

    @property
    def available(self):
        return [
            criterion["criterion"].info()
            for criterion in list(criterions.values())
            if criterion["criterion"]
            .objects.filter(
                for_quality_types=self.quality_type,
                for_quality_use_types=self.quality_use_type,
            )
            .exists()
        ]


class UsesCriterion(models.Model):
    quality = models.ForeignKey(
        Quality, related_name="criterions", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=32)
    version = models.PositiveIntegerField()
    rules = models.PositiveIntegerField()
    weight = models.PositiveIntegerField()

    def __iter__(self):
        criterion_class = get_criterion(self.name)
        criterion = criterion_class["criterion"].objects.get(
            version=self.version
        )
        rules = criterion_class["rules"].objects.get(pk=self.rules)
        data = dict(criterion)
        data.update(
            {
                key: value
                for key, value in list(dict(rules).items())
                if key in criterion.rules or key == "threshold"
            }
        )
        data.update({"weight": self.weight})
        return ((field, value) for field, value in list(data.items()))

    def __str__(self):
        return f"{self.name} for quality {str(self.quality)}"


class QualityCache(models.Model):
    answer = models.PositiveIntegerField(null=True, blank=True)
    hash = models.CharField(max_length=32, unique=True, db_index=True)
    quality = models.FloatField()
    qualities = models.TextField()

    @classmethod
    def get(cls, quality, answer):
        if isinstance(answer, str):
            answer_pk = None
            rationale = answer
        else:
            answer_pk = answer.pk
            rationale = answer.rationale

        criterions = [
            dict(
                chain(
                    iter(
                        get_criterion(c.name)["criterion"].objects.get(
                            version=c.version
                        )
                    ),
                    list({"rules": c.rules, "weight": c.weight}.items()),
                )
            )
            for c in quality.criterions.all()
        ]

        hash_ = hashlib.md5(
            json.dumps({"text": rationale, "criterions": criterions}).encode()
        ).hexdigest()

        if cls.objects.filter(hash=hash_).exists():
            cache = cls.objects.get(hash=hash_)
            return cache.quality, json.loads(cache.qualities)
        else:
            return None, None

    @classmethod
    def cache(cls, quality_instance, answer, quality, qualities):
        if isinstance(answer, str):
            answer_pk = None
            rationale = answer
        else:
            answer_pk = answer.pk
            rationale = answer.rationale

        criterions = [
            dict(
                chain(
                    iter(
                        get_criterion(c.name)["criterion"].objects.get(
                            version=c.version
                        )
                    ),
                    list({"rules": c.rules, "weight": c.weight}.items()),
                )
            )
            for c in quality_instance.criterions.all()
        ]

        hash_ = hashlib.md5(
            json.dumps({"text": rationale, "criterions": criterions}).encode()
        ).hexdigest()

        if not cls.objects.filter(hash=hash_):
            cls.objects.create(
                answer=answer_pk,
                hash=hash_,
                quality=quality,
                qualities=json.dumps(qualities),
            )
