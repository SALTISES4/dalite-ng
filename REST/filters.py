from django_filters import rest_framework as filters


class WildcardFilter(filters.FilterSet):
    def __init__(self, *args, **kwargs):
        field_map = kwargs.pop("field_map")
        super().__init__(*args, **kwargs)
        for k, v in field_map.items():
            _filter = filters.CharFilter(field_name=v, method="wildcard")
            _filter.parent = self
            self.filters[f"{k}__wildcard"] = _filter

    def wildcard(self, queryset, name, value):
        return queryset.filter(
            **{
                f"{name}__icontains": value.replace("*", " ").strip(),
            }
        )
