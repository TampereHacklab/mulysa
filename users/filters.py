import rest_framework_filters as filters

from . import models


class UserFilter(filters.FilterSet):
    class Meta:
        model = models.CustomUser
        fields = {
            'email': ['exact', 'iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'isnull', 'regex', 'iregex'],
            'first_name': ['exact', 'iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'isnull', 'regex', 'iregex'],
            'last_name': ['exact', 'iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'isnull', 'regex', 'iregex'],
            'phone': ['exact', 'iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'isnull', 'regex', 'iregex'],
            'is_active': ['isnull', 'exact'],
            'is_staff': ['isnull', 'exact'],
            'created': ['exact', 'lt', 'gt', 'gte', 'lte', 'range', 'date', 'year', 'iso_year', 'month', 'day', 'week', 'week_day', 'quarter', 'isnull'],
            'last_modified': ['exact', 'lt', 'gt', 'gte', 'lte', 'range', 'date', 'year', 'iso_year', 'month', 'day', 'week', 'week_day', 'quarter', 'isnull'],
            'marked_for_deletion_on': ['exact', 'lt', 'gt', 'gte', 'lte', 'range', 'date', 'year', 'iso_year', 'month', 'day', 'week', 'week_day', 'quarter', 'isnull'],
            'birthday': ['exact', 'lt', 'gt', 'gte', 'lte', 'range', 'year', 'iso_year', 'month', 'day', 'week', 'week_day', 'quarter', 'isnull'],
            'nick': ['exact', 'iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'isnull', 'regex', 'iregex'],
            'municipality': ['exact', 'iexact', 'contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith', 'isnull', 'regex', 'iregex'],
        }
