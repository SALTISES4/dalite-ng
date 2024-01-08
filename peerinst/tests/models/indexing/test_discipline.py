import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from peerinst.models import Discipline


@pytest.mark.django_db
@pytest.mark.parametrize(
    "title, expected_title",
    [
        ("  title  ", "title"),
        ("<script>new title</script>", "new title"),
        ("Discipline", "Discipline"),
        ("dIscIpline", "dIscIpline"),
    ],
)
def test_discipline_save_no_errors(title, expected_title):
    # Act
    discipline = Discipline.objects.create(title=title)

    # Assert
    assert Discipline.objects.filter(title__iexact=expected_title).exists()
    assert discipline.title == expected_title


@pytest.mark.django_db
@pytest.mark.parametrize(
    "title, expected_error, error_message",
    [
        (
            "Discipline-with-hyphen",
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
def test_discipline_save_validation_errors(
    title, expected_error, error_message
):
    # Act & Assert
    with pytest.raises(expected_error) as exc_info:
        Discipline(title=title).full_clean()
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
    Discipline.objects.create(title=title1)

    # Act & Assert
    with pytest.raises(IntegrityError):
        Discipline.objects.create(title=title2)
