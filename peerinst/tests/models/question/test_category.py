import pytest
from django.db import IntegrityError

from peerinst.models import Category


def test_category_custom_save():
    c = Category.objects.create(title="  title  ")

    assert c.title == "title"
    assert not c.title == "  title  "


def test_category_title_bleach():
    c = Category.objects.create(title="<script>new title</script>")

    assert c.title == "new title"


def test_category_title_unique_case_insensitive():
    Category.objects.create(title="Title")
    with pytest.raises(IntegrityError):
        Category.objects.create(title="title")
