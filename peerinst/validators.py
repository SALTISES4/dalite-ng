from better_profanity import profanity
from django.core.validators import BaseValidator, MinLengthValidator
from django.utils.translation import ngettext_lazy
from profanity_check import predict_prob


class MinWordsValidator(MinLengthValidator):
    message = ngettext_lazy(
        "Ensure this value has at least %(limit_value)d word (it has %(show_value)d).",
        "Ensure this value has at least %(limit_value)d words (it has %(show_value)d).",
        "limit_value",
    )
    code = "min_words"

    def clean(self, x):
        return len(str(x).split())


class NoProfanityValidator(BaseValidator):
    """
    The profanity check is twofold:

    - alt-profanity-check is a machine-learning model based on a 200k corpus of human-
      labeled samples and no explicit banned words list.  It is highly performant,
      but won't detect less common variants, like sh1tty.
    - better-profanity has a hard-coded wordlist and is able to check a wider range of
      variants.

    We check probability from alt-profanity-check is less than limit_value and that
    better-profanity results False.

    The better-profanity wordlist is quite conservative and some terms may need to be
    whitelisted.

    The limit_value arg defines the probability threshold below which the passed text
    must be to pass.
    """

    message = ngettext_lazy("", "")
    code = "no_profanity"

    def compare(self, a, b):
        # True values result in a ValidationError
        return a[0] > b or a[1]

    def clean(self, text):
        # Return a tuple with results from both models
        return (
            predict_prob([text])[0],
            profanity.contains_profanity(text),
        )
