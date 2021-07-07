import pytest
from django.db import IntegrityError

from peerinst.models import Category


def test_category_custom_save():
    c = Category.objects.create(title="case sensitive")

    assert c.title == "Case Sensitive"
    assert not c.title == "case sensitive"


def test_category_title_bleach():
    c = Category.objects.create(title="<script>new title</script>")

    assert c.title == "New Title"


def test_category_title_unique_case_insensitive():
    Category.objects.create(title="Case")
    with pytest.raises(IntegrityError):
        Category.objects.create(title="case")
