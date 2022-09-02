import django_filters


class CharInFilter(
    django_filters.filters.BaseInFilter, django_filters.filters.CharFilter
):
    pass
