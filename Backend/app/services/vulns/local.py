import re

from app.models import Confidence, Severity, Vulnerability


def _version_tuple(version: str | None) -> tuple[int, ...] | None:
    if not version:
        return None
    match = re.match(r"\s*(\d+(?:\.\d+)*)", version)
    if not match:
        return None
    return tuple(int(p) for p in match.group(1).split("."))


def _compare(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    a += (0,) * (len(b) - len(a))
    b += (0,) * (len(a) - len(b))
    return (a > b) - (a < b)


def version_at_most(version: str | None, max_version: str) -> bool:
    v = _version_tuple(version)
    m = _version_tuple(max_version)
    if v is None or m is None:
        return False
    return _compare(v, m) <= 0


LOCAL_CVES: list[dict] = [
    {
        "id": "CVE-2023-38408",
        "title": "OpenSSH ssh-agent remote code execution",
        "description": "Remote code execution in ssh-agent via forwarded ssh-agent requests.",
        "severity": Severity.HIGH,
        "cvss": 9.8,
        "match": lambda product, version: product.lower().startswith("openssh") and version_at_most(version, "9.3p1"),
        "references": ["https://nvd.nist.gov/vuln/detail/CVE-2023-38408"],
    },
    {
        "id": "CVE-2016-0777",
        "title": "OpenSSH information leak via roaming",
        "description": "OpenSSH client information leak.",
        "severity": Severity.MEDIUM,
        "cvss": 6.5,
        "match": lambda product, version: product.lower().startswith("openssh") and version_at_most(version, "7.4"),
        "references": ["https://nvd.nist.gov/vuln/detail/CVE-2016-0777"],
    },
    {
        "id": "CVE-2021-41773",
        "title": "Apache HTTP Server path traversal / RCE",
        "description": "Path traversal and RCE in Apache 2.4.49.",
        "severity": Severity.CRITICAL,
        "cvss": 9.8,
        "match": lambda product, version: "apache" in product.lower() and _apache_in_range(version),
        "references": ["https://nvd.nist.gov/vuln/detail/CVE-2021-41773"],
    },
    {
        "id": "CVE-2017-7679",
        "title": "Nginx HTTP/2 remote code execution",
        "description": "Nginx HTTP/2 module remote code execution.",
        "severity": Severity.HIGH,
        "cvss": 8.1,
        "match": lambda product, version: "nginx" in product.lower() and version_at_most(version, "1.11.13"),
        "references": ["https://nvd.nist.gov/vuln/detail/CVE-2017-7679"],
    },
    {
        "id": "CVE-2019-0708",
        "title": "BlueKeep RDP remote code execution",
        "description": "RDP remote code execution in Windows Terminal Services.",
        "severity": Severity.CRITICAL,
        "cvss": 9.8,
        "match": lambda product, version: "terminal" in product.lower() or "rdp" in product.lower(),
        "references": ["https://nvd.nist.gov/vuln/detail/CVE-2019-0708"],
    },
]


def _apache_in_range(version: str | None) -> bool:
    if not version:
        return False
    return version_at_most(version, "2.4.49") and not version_at_most(version, "2.4.48")


def local_lookup(product: str | None, version: str | None) -> list[Vulnerability]:
    if not product:
        return []
    out = []
    for entry in LOCAL_CVES:
        try:
            if entry["match"](product, extract_version_number(version)):
                out.append(
                    Vulnerability(
                        id=entry["id"],
                        title=entry["title"],
                        description=entry["description"],
                        severity=entry["severity"],
                        cvss=entry["cvss"],
                        confidence=Confidence.PROBABLE,
                        references=entry["references"],
                    )
                )
        except Exception:
            continue
    return out


def extract_version_number(version_string: str | None) -> str | None:
    if not version_string:
        return None
    parts = version_string.split()
    for part in parts:
        if re.match(r"^\d", part):
            return part
    return version_string
