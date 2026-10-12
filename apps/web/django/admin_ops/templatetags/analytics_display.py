"""Locale-aware presentation of the analytics API's ISO dates and numeric values."""

from datetime import timezone

from django import template
from django.utils import formats
from django.utils.dateparse import parse_date, parse_datetime

register = template.Library()


@register.filter
def analytics_date(value):
    if not value:
        return "—"
    return formats.date_format(parse_date(value), "SHORT_DATE_FORMAT", use_l10n=True)


@register.filter
def analytics_timestamp(value):
    if not value:
        return "—"
    instant = parse_datetime(value).astimezone(timezone.utc)
    return formats.date_format(instant, "SHORT_DATETIME_FORMAT", use_l10n=True) + " UTC"


@register.filter
def analytics_number(value, decimal_places=0):
    return formats.number_format(value, decimal_pos=int(decimal_places), use_l10n=True, force_grouping=True)
