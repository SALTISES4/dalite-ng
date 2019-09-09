import bleach

from django.template import Library
from django.template.defaultfilters import stringfilter

register = Library()


@register.filter(is_safe=True)
@stringfilter
def bleach_html(text):

    return bleach.clean(
        text,
        tags=[
            "a",
            "abbr",
            "acronym",
            "b",
            "blockquote",
            "br",
            "code",
            "em",
            "i",
            "li",
            "ol",
            "p",
            "strong",
            "ul",
        ],
        styles=[],
        strip=True,
    )
