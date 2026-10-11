from datetime import datetime, timezone

from utils.blocks import block_preview
from utils.markdown import render_markdown


def ensure_tz(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def strftime_filter(value, fmt="%-d %b %Y, %H:%M"):
    value = ensure_tz(value)
    if value is None:
        return "-"
    return value.strftime(fmt)


def to_iso_filter(value):
    value = ensure_tz(value)
    if value is None:
        return ""
    return value.isoformat()


UNITS = (
    (60, 1, "second"),
    (3600, 60, "minute"),
    (86400, 3600, "hour"),
    (604800, 86400, "day"),
    (2629800, 604800, "week"),
    (31557600, 2629800, "month"),
    (None, 31557600, "year"),
)


def span(secs):
    for limit, size, unit in UNITS:
        if limit is None or secs < limit:
            n = secs // size
            return f"{n} {unit}" if n == 1 else f"{n} {unit}s"


def timeago_filter(value):
    value = ensure_tz(value)
    if value is None:
        return "Never"
    secs = int((datetime.now(timezone.utc) - value).total_seconds())
    return f"in {span(-secs)}" if secs < 0 else f"{span(secs)} ago"


def pluralize_filter(n, singular, plural=None):
    if plural is None:
        plural = singular + "s"
    return singular if n == 1 else plural


FILTERS = {
    "strftime": strftime_filter,
    "timeago": timeago_filter,
    "to_iso": to_iso_filter,
    "pluralize": pluralize_filter,
    "markdown": render_markdown,
    "block_preview": block_preview,
}


def register_filters(app):
    for name, fn in FILTERS.items():
        app.template_filter(name)(fn)
