import io
import json

import pytest

from app.core.config import settings
from app.models import Severity
from app.services.vulns import nvd


@pytest.fixture(autouse=True)
def nvd_settings(monkeypatch):
    monkeypatch.setattr(settings, "nvd_enabled", True)
    monkeypatch.setattr(settings, "nvd_api_key", None)
    monkeypatch.setattr(settings, "nvd_min_interval_seconds", 0)
    monkeypatch.setattr(settings, "nvd_cache_ttl_seconds", 900)
    nvd.reset_state()
    yield
    nvd.reset_state()


def _response() -> bytes:
    return json.dumps(
        {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2026-0001",
                        "descriptions": [{"lang": "en", "value": "A critical test vulnerability"}],
                        "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 9.8}}]},
                    }
                }
            ]
        }
    ).encode()


def test_lookup_parses_matches(monkeypatch):
    monkeypatch.setattr(nvd.urllib.request, "urlopen", lambda request, timeout: io.BytesIO(_response()))

    results = nvd.lookup("apache", "2.4.18")

    assert len(results) == 1
    assert results[0].id == "CVE-2026-0001"
    assert results[0].severity is Severity.CRITICAL
    assert results[0].cvss == 9.8


def test_lookup_is_cached_per_product_and_version(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        return io.BytesIO(_response())

    monkeypatch.setattr(nvd.urllib.request, "urlopen", fake_urlopen)

    assert nvd.lookup("apache", "2.4.18")
    assert nvd.lookup("Apache", "2.4.18")

    assert len(calls) == 1


def test_cache_is_disabled_when_ttl_is_zero(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(1)
        return io.BytesIO(_response())

    monkeypatch.setattr(settings, "nvd_cache_ttl_seconds", 0)
    monkeypatch.setattr(nvd.urllib.request, "urlopen", fake_urlopen)

    nvd.lookup("apache", "2.4.18")
    nvd.lookup("apache", "2.4.18")

    assert len(calls) == 2


def test_failures_are_not_cached(monkeypatch):
    calls = []

    def failing_urlopen(request, timeout):
        calls.append(1)
        raise OSError("nvd unavailable")

    monkeypatch.setattr(nvd.urllib.request, "urlopen", failing_urlopen)

    assert nvd.lookup("apache", "2.4.18") == []
    assert nvd.lookup("apache", "2.4.18") == []
    assert len(calls) == 2


def test_disabled_or_missing_product_makes_no_request(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(1)
        return io.BytesIO(_response())

    monkeypatch.setattr(nvd.urllib.request, "urlopen", fake_urlopen)

    assert nvd.lookup(None, "1.0") == []
    monkeypatch.setattr(settings, "nvd_enabled", False)
    assert nvd.lookup("apache", "2.4.18") == []
    assert calls == []
