from django.template import Library

register = Library()


@register.inclusion_tag("admin/peerinst/attribution_stats.html")
def attribution_stats(data):
    return {"data": data}
