import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from peerinst.models import Category, Discipline, Subject


@pytest.mark.django_db
@pytest.mark.parametrize(
    "title, expected_title",
    [
        ("  title  ", "title"),
        ("<script>new title</script>", "new title"),
        ("Subject", "Subject"),
        ("sUbJect", "sUbJect"),
    ],
)
def test_subject_save_no_error_cases(title, expected_title):
    # Arrange
    discipline = Discipline.objects.create(title="Test Discipline")
    category = Category.objects.create(title="Test Category")

    # Act
    subject = Subject.objects.create(discipline=discipline, title=title)
    subject.categories.add(category)

    # Assert
    assert Subject.objects.filter(title__iexact=expected_title).exists()
    assert subject.title == expected_title


@pytest.mark.django_db
@pytest.mark.parametrize(
    "title, expected_error, error_message",
    [
        (
            "Subject-with-hyphen",
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
def test_subject_save_validation_errors(title, expected_error, error_message):
    # Act & Assert
    with pytest.raises(expected_error) as exc_info:
        Subject(title=title).full_clean()
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
    Subject.objects.create(title=title1)

    # Act & Assert
    with pytest.raises(IntegrityError):
        Subject.objects.create(title=title2)
