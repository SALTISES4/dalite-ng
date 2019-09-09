from django import template

register = template.Library()

# https://stackoverflow.com/questions/8000022/django-template-how-to-look-up-a-dictionary-value-with-a-variable
@register.filter
def get_value(dictionary, key):
    return dictionary.get(key)
