from datetime import UTC, datetime, timedelta, timezone

from app.core.time import to_iso_utc


def test_none_stays_none():
    assert to_iso_utc(None) is None


def test_naive_timestamps_are_treated_as_utc():
    value = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC).replace(tzinfo=None)
    assert value.tzinfo is None
    assert to_iso_utc(value) == "2026-01-02T03:04:05+00:00"


def test_aware_timestamps_are_converted_to_utc():
    value = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=2)))
    assert to_iso_utc(value) == "2026-01-02T01:04:05+00:00"


def test_utc_timestamps_keep_their_offset():
    value = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    assert to_iso_utc(value) == "2026-01-02T03:04:05+00:00"
