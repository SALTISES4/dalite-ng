import contextlib
import hashlib
import json
from functools import reduce
from math import exp
from operator import mul, sub

from django.db import models
from django.db.utils import IntegrityError
from django.utils.translation import gettext_lazy as _

from dalite.models.custom_fields import CommaSepField, ProbabilityField
from quality.models.criterion.criterion import Criterion, CriterionRules
from quality.models.quality_type import QualityType, QualityUseType

from .model import create_model


class LikelihoodLanguage(models.Model):
    language = models.CharField(max_length=32, primary_key=True)
    left_to_right = models.BooleanField(default=True)
    n_gram_urls = CommaSepField(distinct=True)

    def __str__(self):
        return str(self.pk)

    @classmethod
    def available(cls):
        return [instance.pk for instance in cls.objects.all()]


class LikelihoodCriterion(Criterion):
    name = models.CharField(
        max_length=32, default="likelihood", editable=False
    )

    @staticmethod
    def info():
        return {
            "name": "likelihood",
            "full_name": _("Readability"),
            "description": _(
                "This does not seem like a well formed sentence."
            ),
        }

    @staticmethod
    def create_default():
        criterion = LikelihoodCriterion.objects.create(
            binary_threshold=False, uses_rules=["languages"]
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
        rules = LikelihoodCriterionRules.objects.get(pk=rules_pk)

        languages = LikelihoodLanguage.objects.all()
        other_languages = languages.exclude(language__in=rules.languages.all())

        language_likelihoods = {
            language.language: LikelihoodCache.get(
                answer, language, rules.max_gram
            )
            for language in languages
        }

        likelihoods = [
            1 - min(1, exp(-sub(*language_likelihoods[language.language])))
            for language in rules.languages.all()
        ] + [
            1
            - min(
                1,
                exp(
                    language_likelihoods[other_language.language][0]
                    - language_likelihoods[language.language][0]
                ),
            )
            for other_language in other_languages
            for language in rules.languages.all()
        ]

        likelihood = reduce(mul, likelihoods, 1) ** (1.0 / len(likelihoods))

        evaluation = {"version": self.version, "quality": likelihood}
        evaluation.update(
            {criterion: val["value"] for criterion, val in rules}
        )
        return evaluation

    def batch_evaluate(self, answers, rules_pk):
        rules = LikelihoodCriterionRules.objects.get(pk=rules_pk)

        languages = LikelihoodLanguage.objects.all()
        other_languages = languages.exclude(language__in=rules.languages.all())

        answers = list(answers)

        language_likelihoods = {
            language.language: LikelihoodCache.batch(
                answers, language, rules.max_gram
            )
            for language in languages
        }

        likelihoods = [
            [
                1
                - min(
                    1, exp(-sub(*language_likelihoods[language.language][i]))
                )
                for language in rules.languages.all()
            ]
            + [
                1
                - min(
                    1,
                    exp(
                        language_likelihoods[other_language.language][i][0]
                        - language_likelihoods[language.language][i][0]
                    ),
                )
                for other_language in other_languages
                for language in rules.languages.all()
            ]
            for i in range(len(answers))
        ]

        likelihood = [reduce(mul, l, 1) ** (1.0 / len(l)) for l in likelihoods]

        evaluations = [
            {"version": self.version, "quality": l} for l in likelihood
        ]

        for evaluation in evaluations:
            evaluation.update(
                {criterion: val["value"] for criterion, val in rules}
            )

        return evaluations


class LikelihoodCriterionRules(CriterionRules):
    languages = models.ManyToManyField(
        LikelihoodLanguage,
        verbose_name="Languages",
        help_text="Accepted languages.",
    )
    max_gram = models.PositiveIntegerField(
        verbose_name="Max gram", help_text="The maximum size of n-gram to use."
    )

    def __str__(self):
        return f"Rules {self.pk} for criterion likelihood"

    @staticmethod
    def get_or_create(threshold=0.95, languages=None, max_gram=3):
        """
        Creates or get the criterion rules.

        Parameters
        ----------
        threshold : float in [0, 1] (default : 0)
            Minimum value for the criterion to pass
        languages : List[str] (default : ["english", "french"])
            Accepted languages

        Returns
        -------
        LikelihoodCriterionRules
            Instance

        Raises
        ------
        ValueError
            If the arguments have invalid values
        """
        if languages is None:
            languages = ["english", "french"]
        if threshold < 0 or threshold > 1:
            raise ValueError("The threshold must be between 0 and 1")
        if not isinstance(languages, list):
            raise ValueError("The languages must be a list")
        if max_gram < 1:
            raise ValueError("The max gram has to be greater than 0")

        try:
            languages = [
                language
                if isinstance(language, LikelihoodLanguage)
                else LikelihoodLanguage.objects.get(language=language.lower())
                for language in languages
            ]
        except LikelihoodLanguage.DoesNotExist:
            raise ValueError(
                f"The language has to be one of {LikelihoodLanguage.available()}"
            )

        criterion = LikelihoodCriterionRules.objects.filter(
            threshold=threshold, max_gram=max_gram
        )
        for language in languages:
            criterion = criterion.filter(languages__pk=language.pk)
            if not criterion:
                criterion = LikelihoodCriterionRules.objects.create(
                    threshold=threshold, max_gram=max_gram
                )
                criterion.languages.set([l.pk for l in languages])
                criterion.save()
                break
        else:
            criterion = criterion.first()

        return criterion


class LikelihoodCache(models.Model):
    answer = models.PositiveIntegerField(null=True, blank=True)
    language = models.ForeignKey(LikelihoodLanguage, on_delete=models.CASCADE)
    hash = models.CharField(max_length=32, unique=True, db_index=True)
    likelihood = ProbabilityField()
    likelihood_random = ProbabilityField()

    @classmethod
    def get(cls, answer, language, max_gram):
        if isinstance(answer, str):
            answer_pk = None
            rationale = answer
        else:
            answer_pk = answer.pk
            rationale = answer.rationale
        hash_ = hashlib.md5(
            json.dumps(
                {
                    "text": rationale,
                    "language": language.language,
                    "max_gram": max_gram,
                }
            ).encode()
        ).hexdigest()
        try:
            cache = cls.objects.get(hash=hash_)
            likelihood = cache.likelihood
            likelihood_random = cache.likelihood_random
        except cls.DoesNotExist:
            predict = create_model(
                language.language,
                language.n_gram_urls,
                language.left_to_right,
                max_gram,
            )
            likelihood, likelihood_random = predict(rationale)
            # Because multiple servers are used, sometimes the likelihood is
            # written to the db by the first server while the second one is
            # computing it. In these cases, the likelihood written to the db
            # will be used.
            try:
                cls.objects.create(
                    answer=answer_pk,
                    language=language,
                    hash=hash_,
                    likelihood=likelihood,
                    likelihood_random=likelihood_random,
                )
            except IntegrityError:
                cache = cls.objects.get(hash=hash_)
                likelihood = cache.likelihood
                likelihood_random = cache.likelihood_random
        return likelihood, likelihood_random

    @classmethod
    def batch(cls, answers, language, max_gram):
        answers = list(answers)
        pks = [
            None if isinstance(answer, str) else answer.pk
            for answer in answers
        ]
        rationales = [
            answer if isinstance(answer, str) else answer.rationale
            for answer in answers
        ]
        hashes = [
            hashlib.md5(
                json.dumps(
                    {
                        "text": rationale,
                        "language": language.language,
                        "max_gram": max_gram,
                    }
                ).encode()
            ).hexdigest()
            for rationale in rationales
        ]

        likelihoods = []
        for hash_ in hashes:
            try:
                cache = cls.objects.get(hash=hash_)
                likelihoods.append((cache.likelihood, cache.likelihood_random))
            except cls.DoesNotExist:
                likelihoods.append(None)

        if not all(likelihoods):
            predict = create_model(
                language.language,
                language.n_gram_urls,
                language.left_to_right,
                max_gram,
            )
            for (i, likelihood), pk, rationale, hash_ in zip(
                enumerate(likelihoods), pks, rationales, hashes
            ):
                if likelihood is None:
                    _likelihood, likelihood_random = predict(rationale)
                    with contextlib.suppress(IntegrityError):
                        cls.objects.create(
                            answer=pk,
                            language=language,
                            hash=hash_,
                            likelihood=_likelihood,
                            likelihood_random=likelihood_random,
                        )
                    likelihoods[i] = (_likelihood, likelihood_random)

        return likelihoods
