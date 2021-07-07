import pytest
from django.db import IntegrityError

from peerinst.models import Subject


def test_subject_custom_save():
    c = Subject.objects.create(title="case sensitive")

    assert c.title == "Case Sensitive"
    assert not c.title == "case sensitive"


def test_subject_title_bleach():
    c = Subject.objects.create(title="<script>new title</script>")

    assert c.title == "New Title"


def test_subject_title_unique_case_insensitive():
    Subject.objects.create(title="Case")
    with pytest.raises(IntegrityError):
        Subject.objects.create(title="case")
