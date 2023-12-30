import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from peerinst.models import Category


@pytest.mark.django_db
@pytest.mark.parametrize(
    "title, expected_title",
    [
        ("  title  ", "title"),
        ("<script>new title</script>", "new title"),
        ("Category", "Category"),
        ("cAtEgOrY", "cAtEgOrY"),
    ],
)
def test_category_save_no_errors(title, expected_title):
    # Act
    category = Category.objects.create(title=title)

    # Assert
    assert Category.objects.filter(title__iexact=expected_title).exists()
    assert category.title == expected_title


@pytest.mark.django_db
@pytest.mark.parametrize(
    "title, expected_error, error_message",
    [
        (
            "Category-with-hyphen",
            ValidationError,
            "Hyphens may not be used in this field.",
        ),
        (
            "",
            ValidationError,
            "This field cannot be blank.",
        ),
        (
            "C" * 101,
            ValidationError,
            "Ensure this value has at most 100 characters (it has 101).",
        ),
    ],
)
def test_category_save_validation_errors(title, expected_error, error_message):
    # Act & Assert
    with pytest.raises(expected_error) as exc_info:
        Category(title=title).full_clean()
    assert exc_info.type is expected_error
    assert error_message in exc_info.value.messages


@pytest.mark.django_db
@pytest.mark.parametrize(
    "title1, title2",
    [
        ("title", "title"),
        ("Title", "title"),
    ],
)
def test_subject_save_integrity_errors(title1, title2):
    # Arrange
    Category.objects.create(title=title1)

    # Act & Assert
    with pytest.raises(IntegrityError):
        Category.objects.create(title=title2)
