from django.core.validators import MinLengthValidator
from django.utils.translation import ngettext_lazy


class MinWordsValidator(MinLengthValidator):
    message = ngettext_lazy(
        "Ensure this value has at least %(limit_value)d word (it has %(show_value)d).",
        "Ensure this value has at least %(limit_value)d words (it has %(show_value)d).",
        "limit_value",
    )
    code = "min_words"

    def clean(self, x):
        return len(str(x).split())
