import pytest
from django.db import IntegrityError

from peerinst.models import Discipline


def test_discipline_custom_save():
    d = Discipline.objects.create(title="case sensitive")

    assert d.title == "Case Sensitive"
    assert not d.title == "case sensitive"


def test_discipline_title_bleach():
    d = Discipline.objects.create(title="<script>new title</script>")

    assert d.title == "New Title"


def test_discipline_title_unique_case_insensitive():
    Discipline.objects.create(title="Case")
    with pytest.raises(IntegrityError):
        Discipline.objects.create(title="case")
