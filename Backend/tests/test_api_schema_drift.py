from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURE = Path(__file__).parent / "fixtures" / "sample_nmap.xml"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _scan_and_analyze(client):
    """Upload fixture and run analysis, returning scan_id."""
    with open(FIXTURE, "rb") as fh:
        resp = client.post("/api/v1/evidence/nmap", files={"file": ("scan.xml", fh, "text/xml")})
    assert resp.status_code == 200, resp.text
    scan_id = resp.json()["scan_id"]
    resp = client.post("/api/v1/analyze", json={"scan_id": scan_id})
    assert resp.status_code == 200, resp.text
    return scan_id


def test_api_assets_schema_matches_frontend_types(client):
    """Schema-drift test: verify the /api/v1/assets endpoint returns
    fields that match the frontend Asset type definition."""
    _scan_and_analyze(client)
    resp = client.get("/api/v1/assets")
    assert resp.status_code == 200, resp.text
    assets = resp.json()
    assert len(assets) > 0, "Expected at least one asset"

    asset = assets[0]
    # Required fields per frontend Asset type
    assert "id" in asset
    assert isinstance(asset["id"], str)
    assert "ip" in asset
    assert isinstance(asset["ip"], str)
    assert "hostname" in asset
    assert asset["hostname"] is None or isinstance(asset["hostname"], str)
    assert "os" in asset
    assert asset["os"] is None or isinstance(asset["os"], str)
    assert "exposure" in asset
    assert isinstance(asset["exposure"], str)
    assert "services" in asset
    assert isinstance(asset["services"], list)

    # services array items
    if asset["services"]:
        svc = asset["services"][0]
        assert "port" in svc
        assert isinstance(svc["port"], int)
        assert "protocol" in svc
        assert isinstance(svc["protocol"], str)
        assert "service" in svc
        assert isinstance(svc["service"], str)
        assert "product" in svc
        assert svc["product"] is None or isinstance(svc["product"], str)
        assert "version" in svc
        assert svc["version"] is None or isinstance(svc["version"], str)
        assert "state" in svc
        assert isinstance(svc["state"], str)

    # metadata field added in this PR
    assert "metadata" in asset
    assert isinstance(asset["metadata"], dict)


def test_api_findings_schema_matches_frontend_types(client):
    """Verify /api/v1/findings response matches frontend Finding type."""
    scan_id = _scan_and_analyze(client)
    resp = client.get("/api/v1/findings", params={"scan_id": scan_id})
    assert resp.status_code == 200, resp.text
    findings = resp.json()
    assert len(findings) > 0, "Expected at least one finding"

    finding = findings[0]
    assert "id" in finding
    assert isinstance(finding["id"], str)
    assert "title" in finding
    assert isinstance(finding["title"], str)
    assert "severity" in finding
    assert finding["severity"] in ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert "risk_score" in finding
    assert isinstance(finding["risk_score"], (int, float))
    assert "confidence" in finding
    assert isinstance(finding["confidence"], str)
    assert "status" in finding
    assert finding["status"] in ("open", "acknowledged", "resolved")
    assert "triage_note" in finding
    assert "triaged_at" in finding

    # affected_service is optional
    if finding.get("affected_service"):
        svc = finding["affected_service"]
        assert "port" in svc
        assert isinstance(svc["port"], int)
        assert "protocol" in svc
        assert isinstance(svc["protocol"], str)
        # service field may be missing or empty depending on scan data
        if svc.get("service"):
            assert isinstance(svc["service"], str)
        # version field may be missing depending on scan data
        if svc.get("version"):
            assert isinstance(svc["version"], str)


def test_api_scans_schema_matches_frontend_types(client):
    """Verify /api/v1/scans response matches frontend Scan type."""
    _scan_and_analyze(client)
    resp = client.get("/api/v1/scans")
    assert resp.status_code == 200, resp.text
    scans = resp.json()
    assert len(scans) > 0, "Expected at least one scan"

    scan = scans[0]
    assert "id" in scan
    assert isinstance(scan["id"], str)
    assert "source" in scan
    assert isinstance(scan["source"], str)
    assert "filename" in scan
    assert scan["filename"] is None or isinstance(scan["filename"], str)
    assert "status" in scan
    assert isinstance(scan["status"], str)
    assert "created_at" in scan
    assert scan["created_at"] is None or isinstance(scan["created_at"], str)
    assert "asset_count" in scan
    assert isinstance(scan["asset_count"], int)
    assert "finding_count" in scan
    assert isinstance(scan["finding_count"], int)