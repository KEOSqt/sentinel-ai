from app.models import Finding, SecurityEvidence
from app.services import normalization, vulns
from app.services.correlation import RULES
from app.services.risk import score_risk


def analyze(evidence: SecurityEvidence) -> list[Finding]:
    """Normalize, look up vulnerabilities, correlate, score. Returns findings."""
    normalized = normalization.normalize_evidence(evidence)
    findings: list[Finding] = []

    for asset in normalized.assets:
        vulns_by_service: dict[tuple[int, str], list] = {}
        for service in asset.services:
            if service.state != "open":
                continue
            vulns_by_service[(service.port, service.protocol)] = vulns.lookup_vulnerabilities(service)

        for rule in RULES:
            findings.extend(rule.evaluate(asset, vulns_by_service))

    for finding in findings:
        finding.risk_score = score_risk(finding.severity, finding.confidence, finding.asset.exposure if finding.asset else "unknown")
        # severity stays as the rule's assessment; risk_score is the quantified priority

    findings.sort(key=lambda f: f.risk_score, reverse=True)
    return findings
