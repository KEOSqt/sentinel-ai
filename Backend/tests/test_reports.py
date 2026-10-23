from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import pipeline
from app.db import ScanRecord


FIXTURE = Path(__file__).parent / "fixtures" / "sample_nmap.xml"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _scan_and_analyze(client):
    """Upload fixture and run analysis, returning scan_id."""
    with open(FIXTURE, "rb") as fh:
        resp = client.post("/api/v1/evidence/nmap",
                           files={"file": ("scan.xml", fh, "text/xml")})
    assert resp.status_code == 200, resp.text
    scan_id = resp.json()["scan_id"]
    resp = client.post("/api/v1/analyze", json={"scan_id": scan_id})
    assert resp.status_code == 200, resp.text
    return scan_id


def test_create_report(client):
    scan_id = _scan_and_analyze(client)
    resp = client.post("/api/v1/reports", json={"scan_id": scan_id})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["scan_id"] == scan_id
    assert "id" in body
    assert "content" in body
    assert "Sentinel-AI Security Report" in body["content"]


def test_create_report_returns_existing(client):
    """Generating a report for the same scan twice should return the same report."""
    scan_id = _scan_and_analyze(client)
    resp1 = client.post("/api/v1/reports", json={"scan_id": scan_id})
    assert resp1.status_code == 200
    body1 = resp1.json()

    resp2 = client.post("/api/v1/reports", json={"scan_id": scan_id})
    assert resp2.status_code == 200
    body2 = resp2.json()
    assert body1["id"] == body2["id"]


def test_get_report(client):
    scan_id = _scan_and_analyze(client)
    create_resp = client.post("/api/v1/reports", json={"scan_id": scan_id})
    report_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/reports/{report_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == report_id
    assert body["scan_id"] == scan_id
    assert "content" in body


def test_get_report_not_found(client):
    resp = client.get("/api/v1/reports/nonexistent-id")
    assert resp.status_code == 404


def test_delete_report(client):
    scan_id = _scan_and_analyze(client)
    create_resp = client.post("/api/v1/reports", json={"scan_id": scan_id})
    report_id = create_resp.json()["id"]

    resp = client.delete(f"/api/v1/reports/{report_id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["detail"] == "Report deleted"

    # Deleted report should now be 404
    resp = client.get(f"/api/v1/reports/{report_id}")
    assert resp.status_code == 404


def test_delete_nonexistent_report(client):
    resp = client.delete("/api/v1/reports/nonexistent-id")
    assert resp.status_code == 404