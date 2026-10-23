from app.models import AIAnalysis, Asset, Finding, Service
from app.services.ai.analyst import (
    _fallback_analysis,
    _infer_attack_paths,
)


def test_fallback_analysis_no_findings():
    """With no findings, fallback should report zero findings and low risk."""
    analysis = _fallback_analysis(assets=[], findings=[])
    assert analysis.summary == "No findings were identified from the provided evidence."
    assert analysis.risk_assessment == "Overall risk is low based on available evidence."
    assert analysis.priority_findings == []
    assert analysis.recommendations == [
        "Collect additional evidence (credentialed scans, logs) to improve coverage."
    ]
    assert analysis.missing_information == [
        "Authentication logs",
        "Vulnerability scan results",
    ]


def test_fallback_analysis_with_findings():
    """With findings, fallback should summarize counts and highest risk."""
    assets = [
        Asset(ip="192.168.1.10", hostname="server01", os="Linux",
              services=[Service(port=22, protocol="tcp", service="ssh")]),
    ]
    findings = [
        Finding(
            id="f-1",
            title="CVE-2023-38408: OpenSSH ssh-agent RCE",
            severity="HIGH",
            risk_score=9.8,
            confidence="possible",
            asset=assets[0],
            affected_service=Service(port=22, protocol="tcp", service="ssh"),
            rationale="OpenSSH version is vulnerable",
            remediation="Upgrade OpenSSH",
            vulnerabilities=[],
        ),
        Finding(
            id="f-2",
            title="CVE-2021-41773: Apache path traversal",
            severity="CRITICAL",
            risk_score=9.1,
            confidence="possible",
            asset=assets[0],
            affected_service=Service(port=80, protocol="tcp", service="http"),
            rationale="Apache version is vulnerable",
            remediation="Upgrade Apache",
            vulnerabilities=[],
        ),
    ]
    analysis = _fallback_analysis(assets=assets, findings=findings)
    assert len(analysis.priority_findings) == 2
    assert analysis.risk_assessment == "Highest risk score observed: 9.8."
    assert analysis.priority_findings == [
        "CVE-2023-38408: OpenSSH ssh-agent RCE",
        "CVE-2021-41773: Apache path traversal",
    ]


def test_infer_attack_paths_rdp():
    """RDP-related findings should produce a BlueKeep attack path."""
    findings = [
        Finding(id="f-1", title="CVE-2019-0708: BlueKeep RDP RCE",
                severity="CRITICAL", risk_score=9.8, confidence="possible",
                asset=None, affected_service=None, rationale="",
                remediation="", references=[], vulnerabilities=[]),
    ]
    paths = _infer_attack_paths(findings)
    assert any("BlueKeep" in p for p in paths)


def test_infer_attack_paths_openssh():
    """OpenSSH findings should produce an SSH attack path."""
    findings = [
        Finding(id="f-1", title="CVE-2016-0777: OpenSSH info leak",
                severity="MEDIUM", risk_score=6.5, confidence="possible",
                asset=None, affected_service=None, rationale="",
                remediation="", references=[], vulnerabilities=[]),
    ]
    paths = _infer_attack_paths(findings)
    assert any("SSH" in p for p in paths)


def test_infer_attack_paths_apache():
    """Apache findings should produce a web server attack path."""
    findings = [
        Finding(id="f-1", title="CVE-2021-41773: Apache path traversal",
                severity="CRITICAL", risk_score=9.8, confidence="possible",
                asset=None, affected_service=None, rationale="",
                remediation="", references=[], vulnerabilities=[]),
    ]
    paths = _infer_attack_paths(findings)
    assert any("web server" in p.lower() for p in paths)


def test_infer_attack_paths_empty():
    """No findings should produce no attack paths."""
    paths = _infer_attack_paths([])
    assert paths == []