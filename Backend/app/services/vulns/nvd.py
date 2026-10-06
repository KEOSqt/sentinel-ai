import json
import urllib.parse
import urllib.request

from app.core.config import settings
from app.models import Confidence, Severity, Vulnerability

NVD_API = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def lookup(product: str | None, version: str | None) -> list[Vulnerability]:
    """Query NVD for keyword-based CVE matches. Returns [] on any failure."""
    if not settings.nvd_enabled or not product:
        return []

    keyword = f"{product} {version}" if version else product
    params = urllib.parse.urlencode({"keywordSearch": keyword, "resultsPerPage": "5"})
    url = f"{NVD_API}?{params}"

    headers = {"User-Agent": "SentinelAI/0.1"}
    if settings.nvd_api_key:
        headers["apiKey"] = settings.nvd_api_key

    try:
        request = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.load(response)
    except Exception:
        return []

    results = []
    for item in data.get("vulnerabilities", []):
        cve = item.get("cve", {})
        metrics = cve.get("metrics", {})
        cvss = None
        for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
            if metrics.get(key):
                try:
                    cvss = float(metrics[key][0]["cvssData"]["baseScore"])
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
