import bleach
from django.template import Library
from django.template.defaultfilters import stringfilter

register = Library()


ALLOWED_TAGS = [
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
    "sub",
    "sup",
]

ALLOWED_ATTR = {
    "a": ["href", "title", "target", "rel"],
    "abbr": ["title"],
    "acronym": ["title"],
}


@register.filter(is_safe=True)
@stringfilter
def bleach_html(text):

    return bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTR,
        styles=[],
        strip=True,
    )
