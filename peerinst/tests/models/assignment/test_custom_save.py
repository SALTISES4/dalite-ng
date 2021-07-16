import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from peerinst.models import Assignment


def test_assignment_textfields_bleach_and_strip():
    fields = ["conclusion_page", "description", "intro_page", "title"]
    a = Assignment(
        **{field: f"  <script>  {field}  </script>  " for field in fields}
    )
    with pytest.raises(ValidationError):
        a.full_clean()
    a.identifier = "unique"
    a.save()

    for field in fields:
        assert getattr(a, field) == field
        assert not getattr(a, field) == f"  <script>  {field}  </script>  "


def test_assignment_id_unique_case_insensitive():
    Assignment.objects.create(identifier="ID")
    with pytest.raises(IntegrityError):
        Assignment.objects.create(identifier="id")


def test_assignment_id_min_length_validator():
    with pytest.raises(ValidationError):
        a = Assignment(identifier="i", title="Test")
        a.full_clean()
