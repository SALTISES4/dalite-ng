import pytest
from django.db import IntegrityError

from peerinst.models import Discipline


def test_discipline_custom_save_strip():
    d = Discipline.objects.create(title="  title  ")

    assert d.title == "title"
    assert not d.title == "  title  "


def test_discipline_title_bleach():
    d = Discipline.objects.create(title="<script>new title</script>")

    assert d.title == "new title"


def test_discipline_title_unique_case_insensitive():
    Discipline.objects.create(title="Title")
    with pytest.raises(IntegrityError):
        Discipline.objects.create(title="title")
