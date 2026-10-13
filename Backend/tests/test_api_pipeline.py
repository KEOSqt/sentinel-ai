import os
from pathlib import Path

os.environ["SENTINEL_DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SENTINEL_NVD_ENABLED"] = "false"

_test_db = Path(__file__).parent.parent / "test.db"
if _test_db.exists():
    _test_db.unlink()

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURE = Path(__file__).parent / "fixtures" / "sample_nmap.xml"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "healthy"}


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


def test_upload_rejects_bad_xml(client):
    resp = client.post("/api/v1/evidence/nmap", files={"file": ("bad.xml", b"<notnmap/>", "text/xml")})
    assert resp.status_code == 422


def test_findings_404(client):
    assert client.get("/api/v1/findings/nonexistent").status_code == 404
