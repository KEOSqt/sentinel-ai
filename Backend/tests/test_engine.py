from app.models import Confidence, Severity
from app.services.correlation import RULES
from app.services.risk import band_for, score_risk
from app.services.vulns.local import local_lookup, version_at_most


def test_version_comparison():
    assert version_at_most("7.2p2", "9.3p1")
    assert not version_at_most("9.4", "9.3p1")
    assert version_at_most("2.4.18", "2.4.49")


def test_local_cve_matching():
    vulns = local_lookup("OpenSSH", "OpenSSH 7.2p2 Ubuntu 4ubuntu2.10")
    ids = [v.id for v in vulns]
    assert "CVE-2023-38408" in ids
    assert "CVE-2016-0777" in ids
    assert local_lookup("UnknownProduct", "1.0") == []


def test_risk_scoring_bounds_and_bands():
    assert score_risk(Severity.CRITICAL, Confidence.CONFIRMED, "public") == 90.0
    assert band_for(score_risk(Severity.CRITICAL, Confidence.CONFIRMED, "public")) == Severity.CRITICAL
    low = score_risk(Severity.LOW, Confidence.UNKNOWN, "internal")
    assert 0 <= low < 20


def test_correlation_rules_registered():
    names = [r.name for r in RULES]
    assert "vulnerable_service" in names
    assert "exposed_rdp" in names
    assert "outdated_service" in names
