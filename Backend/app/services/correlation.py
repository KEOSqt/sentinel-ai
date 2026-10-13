
from app.models import (
    Asset,
    Confidence,
    Evidence,
    Finding,
    Service,
    Severity,
    Vulnerability,
)
from app.services.vulns.local import _extract_version_number, version_at_most


class Rule:
    name = "base"

    def evaluate(self, asset: Asset, vulns_by_service: dict[tuple[int, str], list[Vulnerability]]) -> list[Finding]:
        raise NotImplementedError


class VulnerableServiceRule(Rule):
    name = "vulnerable_service"

    def evaluate(self, asset, vulns_by_service):
        findings = []
        for service in asset.services:
            if service.state != "open":
                continue
            for vuln in vulns_by_service.get((service.port, service.protocol), []):
                findings.append(
                    Finding(
                        title=f"{vuln.id}: {vuln.title}",
                        description=vuln.description or "",
                        severity=vuln.severity,
                        confidence=vuln.confidence,
                        asset=asset,
                        affected_service=service,
                        evidence=[Evidence(source="nmap", evidence_type="service_version", data={"port": service.port, "service": service.service, "version": service.version})],
                        rationale=f"Detected {service.service} version '{service.version}' on port {service.port}/{service.protocol} matches {vuln.id}.",
                        remediation=f"Upgrade {service.product or service.service} to a patched version and review {vuln.id}.",
                        references=vuln.references,
                        vulnerabilities=[vuln],
                    )
                )
        return findings


class ExposedRdpRule(Rule):
    name = "exposed_rdp"

    def evaluate(self, asset, vulns_by_service):
        for service in asset.services:
            if service.state != "open":
                continue
            if service.port == 3389 or "terminal" in (service.product or "").lower() or service.service in ("ms-wbt-server", "rdp"):
                return [
                    Finding(
                        title="Remote Desktop (RDP) exposed",
                        description="RDP is exposed and is a frequent target for brute-force and exploitation.",
                        severity=Severity.HIGH,
                        confidence=Confidence.PROBABLE,
                        asset=asset,
                        affected_service=service,
                        evidence=[Evidence(source="nmap", evidence_type="open_port", data={"port": service.port, "service": service.service})],
                        rationale=f"Port {service.port}/{service.protocol} is open and running RDP; RDP exposure enables brute-force and RCE attacks such as BlueKeep.",
                        remediation="Restrict RDP to a VPN or allowlisted IPs, enable NLA, and keep the host patched.",
                        references=["https://nvd.nist.gov/vuln/detail/CVE-2019-0708"],
                    )
                ]
        return []


class OutdatedServiceRule(Rule):
    name = "outdated_service"

    def evaluate(self, asset, vulns_by_service):
        findings = []
        for service in asset.services:
            if service.state != "open" or not service.version:
                continue
            if vulns_by_service.get((service.port, service.protocol)):
                # CVE rule already covers this exact match
                continue
            product = (service.product or service.service or "").lower()
            ver = _extract_version_number(service.version)
            if not ver:
                continue
            if product.startswith("openssh") and version_at_most(ver, "7.4"):
                findings.append(_outdated(asset, service, Severity.MEDIUM, "Outdated OpenSSH", "Upgrade OpenSSH to the latest supported release."))
            elif "apache" in product and version_at_most(ver, "2.4.18"):
                findings.append(_outdated(asset, service, Severity.MEDIUM, "Outdated Apache httpd", "Upgrade Apache httpd to a supported version."))
        return findings


def _outdated(asset: Asset, service: Service, severity: Severity, title: str, remediation: str) -> Finding:
    return Finding(
        title=title,
        description=f"{service.service} on port {service.port} appears to be running an outdated version ({service.version}).",
        severity=severity,
        confidence=Confidence.POSSIBLE,
        asset=asset,
        affected_service=service,
        evidence=[Evidence(source="nmap", evidence_type="service_version", data={"port": service.port, "version": service.version})],
        rationale=f"Detected version '{service.version}' is below a known-good baseline.",
        remediation=remediation,
        references=[],
    )


RULES: list[Rule] = [VulnerableServiceRule(), ExposedRdpRule(), OutdatedServiceRule()]
