import pytest
from pydantic import ValidationError

from app.core.config import Settings


def _settings(monkeypatch, value: str) -> Settings:
    """Build Settings with SENTINEL_CORS_ORIGINS set to an exact string."""
    monkeypatch.setenv("SENTINEL_CORS_ORIGINS", value)
    return Settings()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # The documented JSON array form.
        ('["http://a.test", "http://b.test"]', ["http://a.test", "http://b.test"]),
        # Comma-separated, which used to crash the app at import time.
        ("http://localhost:3000,http://example.com", ["http://localhost:3000", "http://example.com"]),
        ("http://only.test", ["http://only.test"]),
        ("  http://a.test , http://b.test  ", ["http://a.test", "http://b.test"]),
        # Wildcards and quoting.
        ("*", ["*"]),
        ('"http://quoted.test"', ["http://quoted.test"]),
        ('""', []),
        # Empty values mean "no origins configured".
        ("", []),
        ("   ", []),
    ],
)
def test_cors_origins_accepts_several_formats(monkeypatch, raw, expected):
    assert _settings(monkeypatch, raw).cors_origins == expected


@pytest.mark.parametrize(
    "raw",
    ["[broken", '{"a": 1}', '"unterminated', '["http://a.test", ]'],
)
def test_cors_origins_rejects_nonsense_with_a_readable_message(monkeypatch, raw):
    """Malformed values must fail fast, but say what to do about it."""
    with pytest.raises(ValidationError) as excinfo:
        _settings(monkeypatch, raw)

    message = str(excinfo.value)
    assert "SENTINEL_CORS_ORIGINS" in message


def test_credentials_disabled_for_wildcard(monkeypatch):
    """A wildcard origin plus credentials is invalid per the CORS spec."""
    assert _settings(monkeypatch, "*").cors_allow_credentials is False


def test_credentials_enabled_for_specific_origins(monkeypatch):
    settings = _settings(monkeypatch, "http://localhost:3000,http://example.com")
    assert settings.cors_allow_credentials is True