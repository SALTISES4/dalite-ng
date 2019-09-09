# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest
from django.core.exceptions import ValidationError
from django.db import models
from mixer.backend.django import mixer

from reputation.models import Criterion
from reputation.models.criteria.criterion import validate_list_floats_greater_0


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_dict():
    class FakeCriterion(Criterion):
        name = models.CharField(max_length=32, default="fake", editable=False)

        class Meta:
            app_label = "reputation"

        @staticmethod
        def info():
            return {"name": "fake", "full_name": "fake", "description": "fake"}

    with mixer.ctx(commit=False):
        fake_criterion = mixer.blend(FakeCriterion)

        data = dict(fake_criterion)

        assert len(data) == 8
        assert "version" in data
        assert "points_per_threshold" in data
        assert "thresholds" in data
        assert "badge_thresholds" in data
        assert "badge_colour" in data
        assert "name" in data
        assert "full_name" in data
        assert "description" in data


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_save__missing_name():
    class FakeCriterion(Criterion):
        class Meta:
            app_label = "reputation"

    with mixer.ctx(commit=False):
        fake_criterion = mixer.blend(FakeCriterion)

        with pytest.raises(NotImplementedError):
            fake_criterion.save()


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_save__points_len_equal_thresholds_length():
    class FakeCriterion(Criterion):
        name = models.CharField(max_length=32, default="fake", editable=False)

        class Meta:
            app_label = "reputation"

    with mixer.ctx(commit=False), mock.patch(
        "reputation.models.criteria.criterion.Criterion.save"
    ):
        fake_criterion = mixer.blend(
            FakeCriterion, points_per_threshold="1,2,3", thresholds="1,2,3"
        )

        fake_criterion.save()


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_save__points_len_one_more_than_thresholds_length():
    class FakeCriterion(Criterion):
        name = models.CharField(max_length=32, default="fake", editable=False)

        class Meta:
            app_label = "reputation"

    with mixer.ctx(commit=False), mock.patch(
        "reputation.models.criteria.criterion.Criterion.save"
    ):
        fake_criterion = mixer.blend(
            FakeCriterion, points_per_threshold="1,2,3", thresholds="1,2"
        )

        fake_criterion.save()


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_save__points_len_more_than_one_than_thresholds_length():
    class FakeCriterion(Criterion):
        name = models.CharField(max_length=32, default="fake", editable=False)

        class Meta:
            app_label = "reputation"

    with mixer.ctx(commit=False):
        fake_criterion = mixer.blend(
            FakeCriterion, points_per_threshold="1,2,3", thresholds="1"
        )

        with pytest.raises(ValidationError):
            fake_criterion.save()


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_save__points_len_less_than_thresholds_length():
    class FakeCriterion(Criterion):
        name = models.CharField(max_length=32, default="fake", editable=False)

        class Meta:
            app_label = "reputation"

    with mixer.ctx(commit=False):
        fake_criterion = mixer.blend(
            FakeCriterion, points_per_threshold="1,2", thresholds="1,2,3"
        )

        with pytest.raises(ValidationError):
            fake_criterion.save()


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_info__no_threshold():
    class FakeCriterion(Criterion):
        name = models.CharField(max_length=32, default="fake", editable=False)

        class Meta:
            app_label = "reputation"

        def info(self):
            return super(FakeCriterion, self).info(
                {"name": "test", "full_name": "test", "description": "A test."}
            )

    with mixer.ctx(commit=False):
        fake_criterion = mixer.blend(FakeCriterion)
        fake_criterion.points_per_threshold = [1]
        fake_criterion.thresholds = []

        info = fake_criterion.info()
        assert len(info) == 3
        assert info["description"].startswith(
            "A test. The points are awarded as 1 for each of these."
        )


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_info__same_thresholds():
    class FakeCriterion(Criterion):
        name = models.CharField(max_length=32, default="fake", editable=False)

        class Meta:
            app_label = "reputation"

        def info(self):
            return super(FakeCriterion, self).info(
                {"name": "test", "full_name": "test", "description": "A test."}
            )

    with mixer.ctx(commit=False):
        fake_criterion = mixer.blend(FakeCriterion)
        fake_criterion.points_per_threshold = [1]
        fake_criterion.thresholds = [5]

        info = fake_criterion.info()
        assert len(info) == 3
        assert info["description"].startswith(
            "A test. The points are awarded as 1 for each of these between "
            "0 and 5."
        )


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_info__past_thresholds():
    class FakeCriterion(Criterion):
        name = models.CharField(max_length=32, default="fake", editable=False)

        class Meta:
            app_label = "reputation"

        def info(self):
            return super(FakeCriterion, self).info(
                {"name": "test", "full_name": "test", "description": "A test."}
            )

    with mixer.ctx(commit=False):
        fake_criterion = mixer.blend(FakeCriterion)
        fake_criterion.points_per_threshold = [1, 2]
        fake_criterion.thresholds = [5]

        info = fake_criterion.info()
        assert len(info) == 3
        assert info["description"].startswith(
            "A test. The points are awarded as 1 for each of these between "
            "0 and 5, and 2 for each over 5."
        )


def test_validate_list_floats_greater_0__ok():
    validate_list_floats_greater_0([1.0])
    validate_list_floats_greater_0([1])
    validate_list_floats_greater_0(["1"])


def test_validate_list_floats_greater_0__wrong_type():
    with pytest.raises(ValidationError):
        validate_list_floats_greater_0(["a"])


def test_validate_list_floats_greater_0__smaller_than_0():
    with pytest.raises(ValidationError):
        validate_list_floats_greater_0([0])
        validate_list_floats_greater_0([-1])
