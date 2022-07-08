import re

from django.contrib.admin.widgets import AdminTextareaWidget
from django.core import exceptions
from django.db import models
from django.utils.translation import gettext_lazy as _


class ProbabilityField(models.FloatField):
    description = _("Probability between 0 and 1")
    default_error_messages = {
        "invlid": _("'%(value)s' value must be a float between 0 and 1.")
    }

    def to_python(self, val):
        val = super().to_python(val)
        if not 0 <= val <= 1:
            raise exceptions.ValidationError(
                self.error_messages["invalid"],
                code="invalid",
                params={"value": val},
            )
        return val


class CommaSepField(models.TextField):
    description = _("Comma separated list")
    default_error_messages = {
        "invalid": _("'%(value)s' value must be a comma separated string.")
    }

    def __init__(
        self, distinct=False, separator=",", allowed=None, *args, **kwargs
    ):
        """
        Parameters
        ----------
        distinct : bool (default : False)
            If values should be unique
        separator : str (default : ",")
            Separator used to separate values (not used at the moment)
        allowed : Optional[Tuple[Any]] (default : None)
            Allowed values. If None, all values allowed
        """
        self.distinct = distinct
        self.separator = separator
        self.allowed = allowed
        super().__init__(*args, **kwargs)

    def to_python(self, val):
        if not val:
            return []

        if not isinstance(val, list):
            val = [v.strip() for v in val.split(",")]

        if self.distinct:
            seen = set()
            val = [v for v in val if v not in seen and seen.add(v) is None]

        if self.allowed is not None:
            val = [v for v in val if v in self.allowed]

        return val

    def from_db_value(self, val, *args):
        return self.to_python(val)

    def get_prep_value(self, val):
        if not val:
            return ""
        else:
            return ",".join(val)

    def formfield(self, **kwargs):
        defaults = kwargs
        if defaults["widget"] == AdminTextareaWidget:
            defaults["widget"] = AdminCommaSepFieldWidget
        return super().formfield(**defaults)


class AdminCommaSepFieldWidget(AdminTextareaWidget):
    def format_value(self, val):
        val = super().format_value(val)
        if val is None:
            return ""
        else:
            return ", ".join(
                w.strip()
                for w in re.sub(r"u?'(?!,|\])|'(?=,|\])", "", val[1:-1]).split(
                    ","
                )
            )
