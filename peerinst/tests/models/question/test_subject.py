import pytest
from django.db import IntegrityError

from peerinst.models import Subject


def test_subject_custom_save_strip():
    c = Subject.objects.create(title="  title  ")

    assert c.title == "title"
    assert not c.title == "  title  "


def test_subject_title_bleach():
    c = Subject.objects.create(title="<script>new title</script>")

    assert c.title == "new title"


def test_subject_title_unique_case_insensitive():
    Subject.objects.create(title="Title")
    with pytest.raises(IntegrityError):
        Subject.objects.create(title="title")
