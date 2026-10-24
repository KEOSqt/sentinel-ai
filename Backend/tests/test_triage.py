from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import triage

FIXTURE = Path(__file__).parent / "fixtures" / "sample_nmap.xml"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _scan(client) -> str:
    with open(FIXTURE, "rb") as fh:
        resp = client.post("/api/v1/evidence/nmap", files={"file": ("scan.xml", fh, "text/xml")})
    assert resp.status_code == 200, resp.text
    return resp.json()["scan_id"]


def _analyze(client, scan_id: str):
    resp = client.post("/api/v1/analyze", json={"scan_id": scan_id})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_findings_default_to_open(client):
    scan_id = _scan(client)
    _analyze(client, scan_id)
    # Scoped to this scan: other tests in the suite triage their own findings,
    # and this assertion is about what a freshly analysed scan starts as.
    findings = client.get("/api/v1/findings", params={"scan_id": scan_id}).json()
    assert findings
    assert all(f["status"] == "open" for f in findings)


def test_finding_can_be_acknowledged_and_resolved(client):
    scan_id = _scan(client)
    _analyze(client, scan_id)
    finding_id = client.get("/api/v1/findings").json()[0]["id"]

    resp = client.patch(f"/api/v1/findings/{finding_id}", json={"status": "acknowledged", "note": "tracked in TICKET-1"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "acknowledged"
    assert body["triage_note"] == "tracked in TICKET-1"

    detail = client.get(f"/api/v1/findings/{finding_id}").json()
    assert detail["status"] == "acknowledged"
    assert detail["triage_note"] == "tracked in TICKET-1"

    resp = client.patch(f"/api/v1/findings/{finding_id}", json={"status": "resolved"})
    assert resp.json()["status"] == "resolved"
    # Updating status without a note clears the old one rather than keeping it.
    assert resp.json()["triage_note"] == ""


def test_findings_can_be_filtered_by_status(client):
    scan_id = _scan(client)
    _analyze(client, scan_id)
    findings = client.get("/api/v1/findings").json()
    target = findings[0]["id"]

    client.patch(f"/api/v1/findings/{target}", json={"status": "resolved"})

    resolved = client.get("/api/v1/findings", params={"status": "resolved"}).json()
    # The database persists across tests in this module, so assert membership
    # rather than an exact list.
    assert target in [f["id"] for f in resolved]
    assert all(f["status"] == "resolved" for f in resolved)

    open_ones = client.get("/api/v1/findings", params={"status": "open"}).json()
    assert target not in [f["id"] for f in open_ones]
    assert all(f["status"] == "open" for f in open_ones)


def test_findings_can_be_filtered_by_scan(client):
    scan_a = _scan(client)
    _analyze(client, scan_a)
    scan_b = _scan(client)
    _analyze(client, scan_b)

    for_a = client.get("/api/v1/findings", params={"scan_id": scan_a}).json()
    assert for_a
    assert all(f["scan_id"] == scan_a for f in for_a)

    everything = client.get("/api/v1/findings").json()
    ids_a = {f["id"] for f in for_a}
    assert ids_a <= {f["id"] for f in everything}
    assert any(f["scan_id"] == scan_b for f in everything)
    assert len(everything) > len(for_a)


def test_invalid_status_is_rejected(client):
    finding_id = client.get("/api/v1/findings").json()[0]["id"]
    resp = client.patch(f"/api/v1/findings/{finding_id}", json={"status": "not-a-status"})
    assert resp.status_code == 422


def test_update_unknown_finding_is_404(client):
    assert client.patch("/api/v1/findings/nope", json={"status": "open"}).status_code == 404


def test_triage_survives_reanalysis(client):
    """The whole point of keying on a fingerprint.

    Finding ids are regenerated on every analysis run, so an id-keyed triage
    row would be silently orphaned here.
    """
    scan_id = _scan(client)
    _analyze(client, scan_id)

    before = client.get("/api/v1/findings", params={"scan_id": scan_id}).json()
    target = before[0]
    title = target["title"]
    client.patch(f"/api/v1/findings/{target['id']}", json={"status": "acknowledged", "note": "keep me"})

    _analyze(client, scan_id)  # re-run on the same scan

    after = client.get("/api/v1/findings", params={"scan_id": scan_id}).json()
    same = [f for f in after if f["title"] == title]
    assert same, "the finding should still exist after re-analysis"
    assert same[0]["id"] != target["id"], "ids are expected to change; that is the hazard"
    assert same[0]["status"] == "acknowledged"
    assert same[0]["triage_note"] == "keep me"


def test_fingerprint_is_stable_and_distinct():
    finding = {
        "title": "CVE-1: thing",
        "asset": {"ip": "10.0.0.1"},
        "affected_service": {"port": 22, "protocol": "tcp"},
    }
    same = {**finding, "id": "different-uuid"}
    other = {**finding, "title": "CVE-2: other"}

    assert triage.finding_key("scan", finding) == triage.finding_key("scan", same)
    assert triage.finding_key("scan", finding) != triage.finding_key("scan", other)
    assert triage.finding_key("scan", finding) != triage.finding_key("other-scan", finding)


def test_fingerprint_tolerates_missing_fields():
    """A finding with no asset or service must still produce a key."""
    assert triage.finding_key("scan", {"title": "bare"})
    assert triage.finding_key("scan", {"title": "bare", "asset": None, "affected_service": None})