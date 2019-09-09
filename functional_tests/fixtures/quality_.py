import pytest

from quality.models import Quality, UsesCriterion
from quality.tests.fixtures import *  # noqa


@pytest.fixture
def quality_min_words(min_words_criterion, min_words_rules):
    quality = Quality.objects.get(
        quality_type__type="global", quality_use_type__type="validation"
    )
    min_words_rules.min_words = 3
    min_words_rules.save()
    UsesCriterion.objects.create(
        quality=quality,
        name="min_words",
        version=min_words_criterion.version,
        rules=min_words_rules.pk,
        weight=1,
    )
