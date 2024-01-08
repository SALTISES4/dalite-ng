import bleach
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


def no_hyphens(value):
    """
    Raise a ValidationError if the given value contains hyphens.

    Args:
        value: The value to be checked for hyphens.

    Raises:
        ValidationError: If the value contains hyphens.
    """
    if "-" in value:
        raise ValidationError(_("Hyphens may not be used in this field."))


class Category(models.Model):
    """
    Represents categories (or 'tags') by which questions may be indexed.

    Fields:
        title: The title of the category.  Must be unique.

    Methods:
        save: Saves the category after cleaning the title using bleach.

    TODO: Is no_hyphens validator still needed?
    """

    title = models.CharField(
        _("Category"),
        unique=True,
        max_length=100,
        validators=[no_hyphens],
    )

    class Meta:
        ordering = ("title",)
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Bleach title.

        Remove:
            - all html tags
            - any leading and trailing whitespace.
        """
        self.title = bleach.clean(
            self.title,
            tags=[],
            strip=True,
        ).strip()

        super().save(*args, **kwargs)


class Subject(models.Model):
    """
    Represents subjects by which questions may be indexed.

    Fields:
        title: The title of the subject.  Must be unique.
        discipline: Discipline
        categories: List[Category]

    Methods:
        save: Saves the subject after cleaning the title using bleach.

    TODO: Is no_hyphens validator still needed?
    """

    title = models.CharField(
        _("Subject"),
        unique=True,
        max_length=100,
        validators=[no_hyphens],
    )
    discipline = models.ForeignKey(
        "Discipline", blank=True, null=True, on_delete=models.SET_NULL
    )
    categories = models.ManyToManyField(
        Category, related_name="subjects", blank=True
    )

    class Meta:
        ordering = ("title",)
        verbose_name = _("subject")
        verbose_name_plural = _("subjects")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Bleach title.

        Remove:
            - all html tags
            - any leading and trailing whitespace.
        """
        self.title = bleach.clean(
            self.title,
            tags=[],
            strip=True,
        ).strip()

        super().save(*args, **kwargs)


class Discipline(models.Model):
    """
    Represents disciplines by which questions may be indexed.

    Fields:
        title: The title of the discipline.  Must be unique.

    Methods:
        save: Saves the discipline after cleaning the title using bleach.

    TODO: Is no_hyphens validator still needed?
    """

    title = models.CharField(
        _("Discipline"),
        unique=True,
        max_length=100,
        validators=[no_hyphens],
    )

    class Meta:
        ordering = ("title",)
        verbose_name = _("discipline")
        verbose_name_plural = _("disciplines")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Bleach title.

        Remove:
            - all html tags
            - any leading and trailing whitespace.
        """
        self.title = bleach.clean(
            self.title,
            tags=[],
            strip=True,
        ).strip()
        super().save(*args, **kwargs)
