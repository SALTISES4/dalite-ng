# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from peerinst.tests.fixtures import *  # noqa
from quality.models import QualityCache
from quality.tests.fixtures import *  # noqa


def test_cache(global_validation_quality, answers):
    answer = answers[0]
    answer.rationale = "test"
    answer.save()

    quality = 1
    qualities = {"name": "test", "quality": 1, "threshold": 1}

    n = QualityCache.objects.count()
    QualityCache.cache(global_validation_quality, answer, quality, qualities)
    QualityCache.cache(
        global_validation_quality, answer.rationale, quality, qualities
    )
    assert QualityCache.objects.count() == n + 1


def test_get(global_validation_quality, answers):
    answer = answers[0]
    answer.rationale = "test"
    answer.save()

    quality = 1
    qualities = {"name": "test", "quality": 1, "threshold": 1}

    n = QualityCache.objects.count()
    QualityCache.cache(global_validation_quality, answer, quality, qualities)
    QualityCache.cache(
        global_validation_quality, answer.rationale, quality, qualities
    )
    assert QualityCache.objects.count() == n + 1

    quality_, qualities_ = QualityCache.get(global_validation_quality, answer)
    assert quality_ == quality
    assert qualities_ == qualities
    quality_, qualities_ = QualityCache.get(
        global_validation_quality, answer.rationale
    )
    assert quality_ == quality
    assert qualities_ == qualities
