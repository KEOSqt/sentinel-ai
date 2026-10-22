from datetime import UTC, datetime


def to_iso_utc(value: datetime | None) -> str | None:
    """Serialize a timestamp with an explicit UTC offset.

    SQLite returns naive datetimes even when the value was stored as UTC, and
    browsers interpret offset-less ISO strings as local time.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()
