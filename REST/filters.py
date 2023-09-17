from django_filters import rest_framework as filters


class TitleWildcardFilter(filters.FilterSet):
    title__wildcard = filters.CharFilter(field_name="title", method="wildcard")

    def wildcard(self, queryset, name, value):
        return queryset.filter(
            **{
                f"{name}__icontains": value.replace("*", " ").strip(),
            }
        )


class UsernameWildcardFilter(filters.FilterSet):
    username__wildcard = filters.CharFilter(
        field_name="user__username", method="wildcard"
    )

    def wildcard(self, queryset, name, value):
        return queryset.filter(
            **{
                f"{name}__icontains": value.replace("*", " ").strip(),
            }
        )
