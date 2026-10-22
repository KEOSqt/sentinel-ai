import json
import threading
import time
import urllib.parse
import urllib.request

from app.core.config import settings
from app.models import Confidence, Severity, Vulnerability

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"
MAX_CACHE_ENTRIES = 512

_cache: dict[tuple[str, str | None], tuple[float, list[Vulnerability]]] = {}
_cache_lock = threading.Lock()
_rate_lock = threading.Lock()
_last_request_at = 0.0


def reset_state() -> None:
    """Clear cached lookups and rate-limit state (used by tests)."""
    global _last_request_at
    with _cache_lock:
        _cache.clear()
    with _rate_lock:
        _last_request_at = 0.0


def _cache_get(key: tuple[str, str | None]) -> list[Vulnerability] | None:
    ttl = settings.nvd_cache_ttl_seconds
    if ttl <= 0:
        return None
    with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        stored_at, value = entry
        if time.monotonic() - stored_at > ttl:
            _cache.pop(key, None)
            return None
        return list(value)


def _cache_set(key: tuple[str, str | None], value: list[Vulnerability]) -> None:
    if settings.nvd_cache_ttl_seconds <= 0:
        return
    with _cache_lock:
        if len(_cache) >= MAX_CACHE_ENTRIES:
            _cache.clear()
        _cache[key] = (time.monotonic(), list(value))


def _respect_rate_limit() -> None:
    global _last_request_at
    interval = settings.nvd_min_interval_seconds
    if interval <= 0:
        return
    with _rate_lock:
        elapsed = time.monotonic() - _last_request_at
        if elapsed < interval:
            time.sleep(interval - elapsed)
        _last_request_at = time.monotonic()


def lookup(product: str | None, version: str | None) -> list[Vulnerability]:
    """Query NVD for keyword-based CVE matches. Returns [] on any failure."""
    if not settings.nvd_enabled or not product:
        return []

    key = (product.strip().lower(), (version or "").strip().lower() or None)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    keyword = f"{product} {version}" if version else product
    params = urllib.parse.urlencode({"keywordSearch": keyword, "resultsPerPage": "5"})
    url = f"{NVD_API}?{params}"

    headers = {"User-Agent": "SentinelAI/0.1"}
    if settings.nvd_api_key:
        headers["apiKey"] = settings.nvd_api_key

    _respect_rate_limit()
    try:
        request = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.load(response)
    except Exception:
        return []

    if not isinstance(data, dict):
        return []

    results = []
    for item in data.get("vulnerabilities", []):
        cve = item.get("cve", {})
        metrics = cve.get("metrics", {})
        cvss = None
        for metric_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            if metrics.get(metric_key):
                try:
                    cvss = float(metrics[metric_key][0]["cvssData"]["baseScore"])
                except (KeyError, IndexError, TypeError, ValueError):
                    pass
                break
        descriptions = cve.get("descriptions", [])
        description = next((d.get("value") for d in descriptions if d.get("lang") == "en"), None)
        severity = Severity.MEDIUM
        if cvss is not None:
            severity = _severity_from_cvss(cvss)
        results.append(
            Vulnerability(
                id=cve.get("id", "UNKNOWN"),
                title=(description or cve.get("id", "Unknown"))[:200],
                description=description,
                severity=severity,
                cvss=cvss,
                confidence=Confidence.POSSIBLE,
                references=[f"https://nvd.nist.gov/vuln/detail/{cve.get('id')}"],
            )
        )
    _cache_set(key, results)
    return results


def _severity_from_cvss(cvss: float) -> Severity:
    if cvss >= 9.0:
        return Severity.CRITICAL
    if cvss >= 7.0:
        return Severity.HIGH
    if cvss >= 4.0:
        return Severity.MEDIUM
    if cvss >= 0.1:
        return Severity.LOW
    return Severity.INFO
