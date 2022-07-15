from unittest import mock

import pytest
from django.db import models
from mixer.backend.django import mixer

from quality.models import Criterion


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_info():
    class FakeCriterion(Criterion):
        name = models.CharField(max_length=32, default="fake", editable=False)

        class Meta:
            app_label = "quality"

    with mixer.ctx(commit=False):
        fake_criterion = mixer.blend(FakeCriterion)

        with pytest.raises(NotImplementedError):
            fake_criterion.info()


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_create_default():
    class FakeCriterion(Criterion):
        name = models.CharField(max_length=32, default="fake", editable=False)

        class Meta:
            app_label = "quality"

    with mixer.ctx(commit=False):
        fake_criterion = mixer.blend(FakeCriterion)

        with pytest.raises(NotImplementedError):
            fake_criterion.create_default()


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_evaluate():
    class FakeCriterion(Criterion):
        name = models.CharField(max_length=32, default="fake", editable=False)

        class Meta:
            app_label = "quality"

    with mixer.ctx(commit=False):
        fake_criterion = mixer.blend(FakeCriterion)

        with pytest.raises(NotImplementedError):
            fake_criterion.evaluate(None, None)


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_batch_evaluate():
    class FakeCriterion(Criterion):
        name = models.CharField(max_length=32, default="fake", editable=False)

        class Meta:
            app_label = "quality"

    with mixer.ctx(commit=False):
        fake_criterion = mixer.blend(FakeCriterion)

        with pytest.raises(NotImplementedError):
            fake_criterion.batch_evaluate(None, None)


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_save():
    class FakeCriterion(Criterion):
        class Meta:
            app_label = "quality"

    with mixer.ctx(commit=False):
        fake_criterion = mixer.blend(FakeCriterion)

        with pytest.raises(NotImplementedError):
            fake_criterion.save()


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_rules():
    class FakeCriterion(Criterion):
        name = models.CharField(max_length=32, default="fake", editable=False)

        class Meta:
            app_label = "quality"

    with mixer.ctx(commit=False), mock.patch(
        "quality.models.criterion.criterion.models.Model.save"
    ):
        fake_criterion = mixer.blend(FakeCriterion)

        fake_criterion.uses_rules = ["a", "b", "c", "d"]
        fake_criterion.save()
        assert fake_criterion.rules == ["a", "b", "c", "d"]
