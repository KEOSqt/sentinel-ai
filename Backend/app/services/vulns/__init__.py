from app.models import Confidence, Service, Vulnerability
from app.services.vulns import local, nvd


def lookup_vulnerabilities(service: Service) -> list[Vulnerability]:
    """Local dataset first; augment with NVD when available. Dedupe by CVE id."""
    product = service.product or service.service
    version = service.version

    merged: dict[str, Vulnerability] = {}
    for vuln in local.local_lookup(product, version):
        merged[vuln.id] = vuln
    for vuln in nvd.lookup(product, version):
        merged.setdefault(vuln.id, vuln)

    # Local matches are more reliable for these version checks
    for vuln in merged.values():
        if vuln.confidence == Confidence.UNKNOWN:
            vuln.confidence = Confidence.POSSIBLE

    return list(merged.values())
