from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURE = Path(__file__).parent / "fixtures" / "sample_nmap.xml"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _upload_and_analyze(client) -> tuple[str, dict]:
    with open(FIXTURE, "rb") as fh:
        resp = client.post("/api/v1/evidence/nmap", files={"file": ("scan.xml", fh, "text/xml")})
    assert resp.status_code == 200, resp.text
    scan_id = resp.json()["scan_id"]

    resp = client.post("/api/v1/analyze", json={"scan_id": scan_id})
    assert resp.status_code == 200, resp.text
    return scan_id, resp.json()


def test_health(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "healthy"
    assert body["database"] is True
    assert "llm_provider" in body


def test_health_alias_matches_versioned_route(client):
    assert client.get("/health").json() == client.get("/api/v1/health").json()


def test_cors_does_not_send_wildcard_with_credentials(client):
    resp = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})
    allow_origin = resp.headers.get("access-control-allow-origin")
    assert allow_origin is not None
    assert allow_origin != "*"
    assert resp.headers.get("access-control-allow-credentials") == "true"


def test_cors_disallows_unknown_origin(client):
    resp = client.get("/api/v1/health", headers={"Origin": "http://evil.example"})
    assert resp.headers.get("access-control-allow-origin") != "http://evil.example"


def test_full_pipeline(client):
    with open(FIXTURE, "rb") as fh:
        resp = client.post("/api/v1/evidence/nmap", files={"file": ("scan.xml", fh, "text/xml")})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    scan_id = body["scan_id"]
    assert body["asset_count"] == 2

    resp = client.post("/api/v1/analyze", json={"scan_id": scan_id})
    assert resp.status_code == 200, resp.text
    analysis = resp.json()
    assert analysis["finding_count"] > 0
    assert analysis["analysis"]["summary"]

    assets = client.get("/api/v1/assets").json()
    assert len(assets) == 2

    findings = client.get("/api/v1/findings").json()
    assert len(findings) == analysis["finding_count"]

    first = findings[0]
    resp = client.get(f"/api/v1/findings/{first['id']}")
    assert resp.status_code == 200

    resp = client.post("/api/v1/reports", json={"scan_id": scan_id})
    assert resp.status_code == 200
    report_id = resp.json()["id"]

    resp = client.get(f"/api/v1/reports/{report_id}")
    assert resp.status_code == 200
    assert "Sentinel-AI Security Report" in resp.json()["content"]


def test_analysis_is_stored_once_not_on_every_finding(client):
    """The AI analysis belongs to the scan, not to each finding."""
    _, analysis = _upload_and_analyze(client)
    assert analysis["finding_count"] > 1, "fixture should produce multiple findings"

    # The list endpoint must not repeat the blob per finding.
    listed = client.get("/api/v1/findings").json()
    assert all("ai_analysis" not in f for f in listed)

    # ...but the detail endpoint still returns it, for the frontend's detail view.
    detail = client.get(f"/api/v1/findings/{listed[0]['id']}").json()
    assert detail["ai_analysis"]["summary"]


def test_reports_are_listable(client):
    scan_id, _ = _upload_and_analyze(client)
    created = client.post("/api/v1/reports", json={"scan_id": scan_id}).json()

    listed = client.get("/api/v1/reports").json()
    assert any(r["id"] == created["id"] for r in listed)
    # Metadata only; the markdown body is fetched separately.
    assert "content" not in listed[0]

    filtered = client.get("/api/v1/reports", params={"scan_id": scan_id}).json()
    assert all(r["scan_id"] == scan_id for r in filtered)


def test_scan_detail_404(client):
    assert client.get("/api/v1/scans/nonexistent").status_code == 404


def test_scan_detail_before_analysis(client):
    """An uploaded-but-unanalysed scan still shows its evidence, with no findings.

    This is the state every scan passes through on the way in; the detail page
    has to render it rather than treat "no analysis yet" as an error.
    """
    with open(FIXTURE, "rb") as fh:
        resp = client.post("/api/v1/evidence/nmap", files={"file": ("scan.xml", fh, "text/xml")})
    scan_id = resp.json()["scan_id"]

    body = client.get(f"/api/v1/scans/{scan_id}").json()
    assert body["scan"]["id"] == scan_id
    assert body["scan"]["status"] == "ingested"
    assert len(body["assets"]) == body["scan"]["asset_count"]
    assert body["findings"] == []
    assert body["analysis"] is None
    assert body["counts"] == {"open": 0, "acknowledged": 0, "resolved": 0}


def test_scan_detail_after_analysis(client):
    scan_id, analysis = _upload_and_analyze(client)
    body = client.get(f"/api/v1/scans/{scan_id}").json()

    assert body["scan"]["status"] == "completed"
    assert body["scan"]["finding_count"] == analysis["finding_count"]
    assert body["analysis"]["summary"]
    # Every finding belongs to this scan and starts out open.
    assert all(f["scan_id"] == scan_id for f in body["findings"])
    assert all(f["status"] == "open" for f in body["findings"])
    assert sum(body["counts"].values()) == len(body["findings"])
    assert len(body["assets"]) == body["scan"]["asset_count"]


def test_scan_detail_scopes_findings_to_its_own_scan(client):
    """Two scans of the same file must not bleed findings into each other."""
    first_id, first = _upload_and_analyze(client)
    second_id, second = _upload_and_analyze(client)
    assert first_id != second_id
    assert first["finding_count"] == second["finding_count"]

    body = client.get(f"/api/v1/scans/{first_id}").json()
    assert len(body["findings"]) == first["finding_count"]
    assert all(f["scan_id"] == first_id for f in body["findings"])


def test_upload_rejects_bad_xml(client):
    resp = client.post("/api/v1/evidence/nmap", files={"file": ("bad.xml", b"<notnmap/>", "text/xml")})
    assert resp.status_code == 422


def test_findings_404(client):
    assert client.get("/api/v1/findings/nonexistent").status_code == 404


def test_reports_404(client):
    assert client.get("/api/v1/reports/nonexistent").status_code == 404