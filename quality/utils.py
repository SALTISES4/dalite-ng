from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_text
from django.utils.functional import Promise


# https://stackoverflow.com/questions/19734724/django-is-not-json-serializable-when-using-ugettext-lazy
class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super().default(obj)
