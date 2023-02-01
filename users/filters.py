import datetime as dt

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

import rest_framework_filters as filters

from . import models


class PredefAgeListFilter(admin.SimpleListFilter):
    title = _("Age")
    parameter_name = "age"

    def lookups(self, request, model_admin):
        """
        Few predefined filters
        """
        return (
            ("under18", _("Under 18 years")),
            ("over18", _("Over 18 years")),
            ("under30", _("Under 30 years")),
            ("20to50", _("20 to 60")),
            ("over63", _("Over 63 years")),
        )

    def queryset(self, request, queryset):
        """
        filter the queryset
        """
        today = dt.date.today()

        if self.value() == "under18":
            return queryset.filter(birthday__gte=self._add_years(today, -18))
        if self.value() == "over18":
            return queryset.filter(birthday__lte=self._add_years(today, -18))
        if self.value() == "under30":
            return queryset.filter(birthday__gte=self._add_years(today, -30))
        if self.value() == "20to50":
            return queryset.filter(birthday__lte=self._add_years(today, -20)).filter(
                birthday__gte=self._add_years(today, -60)
            )
        if self.value() == "over63":
            return queryset.filter(birthday__lte=self._add_years(today, -63))

    def _add_years(self, dt, years):
        try:
            dt = dt.replace(year=dt.year + years)
        except ValueError:
            dt = dt.replace(year=dt.year + years, day=dt.day - 1)
        return dt


class UserFilter(filters.FilterSet):
    class Meta:
        model = models.CustomUser
        fields = {
            "email": [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "isnull",
                "regex",
                "iregex",
            ],
            "first_name": [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "isnull",
                "regex",
                "iregex",
            ],
            "last_name": [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "isnull",
                "regex",
                "iregex",
            ],
            "phone": [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "isnull",
                "regex",
                "iregex",
            ],
            "is_active": ["isnull", "exact"],
            "is_staff": ["isnull", "exact"],
            "created": [
                "exact",
                "lt",
                "gt",
                "gte",
                "lte",
                "range",
                "date",
                "year",
                "iso_year",
                "month",
                "day",
                "week",
                "week_day",
                "quarter",
                "isnull",
            ],
            "last_modified": [
                "exact",
                "lt",
                "gt",
                "gte",
                "lte",
                "range",
                "date",
                "year",
                "iso_year",
                "month",
                "day",
                "week",
                "week_day",
                "quarter",
                "isnull",
            ],
            "marked_for_deletion_on": [
                "exact",
                "lt",
                "gt",
                "gte",
                "lte",
                "range",
                "date",
                "year",
                "iso_year",
                "month",
                "day",
                "week",
                "week_day",
                "quarter",
                "isnull",
            ],
            "birthday": [
                "exact",
                "lt",
                "gt",
                "gte",
                "lte",
                "range",
                "year",
                "iso_year",
                "month",
                "day",
                "week",
                "week_day",
                "quarter",
                "isnull",
            ],
            "nick": [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "isnull",
                "regex",
                "iregex",
            ],
            "municipality": [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
                "isnull",
                "regex",
                "iregex",
            ],
        }
