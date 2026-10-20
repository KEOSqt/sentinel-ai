from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes.assets import _scan_views
from app.db import ScanRecord
from app.main import app
from app.models import Asset, SecurityEvidence

FIXTURE = Path(__file__).parent / "fixtures" / "sample_nmap.xml"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _upload(client, analyzed: bool = True) -> tuple[str, str]:
    """Upload the fixture and return (scan_id, first asset ip)."""
    with open(FIXTURE, "rb") as fh:
        resp = client.post("/api/v1/evidence/nmap", files={"file": ("scan.xml", fh, "text/xml")})
    assert resp.status_code == 200, resp.text
    scan_id = resp.json()["scan_id"]
    if analyzed:
        resp = client.post("/api/v1/analyze", json={"scan_id": scan_id})
        assert resp.status_code == 200, resp.text
    assets = client.get("/api/v1/assets").json()
    return scan_id, assets[0]["ip"]


def test_list_still_returns_every_host(client):
    # Hosts come from the uploaded evidence, so they are visible before any
    # analysis has run.
    _upload(client, analyzed=False)
    assets = client.get("/api/v1/assets").json()
    assert assets
    for asset in assets:
        assert asset["ip"]
        assert isinstance(asset["services"], list)
    # The fixture holds two hosts, and other tests upload it again; the list
    # de-duplicates by IP rather than growing with every upload.
    assert len({a["ip"] for a in assets}) == len(assets)


def test_unknown_asset_is_404(client):
    resp = client.get("/api/v1/assets/203.0.113.99")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Asset not found"


def test_asset_detail_reports_provenance_and_findings(client):
    _upload(client)
    details = [
        client.get(f"/api/v1/assets/{asset['ip']}").json()
        for asset in client.get("/api/v1/assets").json()
    ]
    assert details
    # Which host raises findings is up to the correlation rules, so ask for a
    # host that has some rather than assuming it is the first one.
    body = next((d for d in details if d["findings"]), None)
    assert body is not None, "the fixture should raise at least one finding"

    assert body["asset"]["ip"]
    assert body["scans"], "the host must be attributed to at least one scan"
    for scan in body["scans"]:
        assert scan["id"]
        assert scan["created_at"]
    assert body["first_seen"]
    assert body["last_seen"]
    assert set(body["counts"]) == {"open", "acknowledged", "resolved"}
    assert sum(body["counts"].values()) == len(body["findings"])


def test_asset_detail_findings_all_belong_to_that_host(client):
    """Every finding shown must actually name this host as its asset."""
    _upload(client)
    everything = client.get("/api/v1/findings").json()

    for asset in client.get("/api/v1/assets").json():
        body = client.get(f"/api/v1/assets/{asset['ip']}").json()
        for finding in body["findings"]:
            assert (finding.get("asset") or {}).get("ip") == asset["ip"]
            # The detail endpoint reuses the list payload, so triage must be
            # visible here too, not just on /findings.
            assert "status" in finding
            assert "scan_id" in finding

        # A host's findings are a subset of all findings, never a new kind.
        all_ids = {f["id"] for f in everything}
        assert {f["id"] for f in body["findings"]} <= all_ids

        # Counts must account for exactly the findings being shown.
        assert sum(body["counts"].values()) == len(body["findings"])


def test_asset_counts_follow_triage_decisions(client):
    _upload(client)
    findings = client.get("/api/v1/findings").json()
    assert findings, "the fixture should raise findings"
    target = findings[0]
    ip = target["asset"]["ip"]

    resp = client.patch(f"/api/v1/findings/{target['id']}", json={"status": "resolved", "note": "patched"})
    assert resp.status_code == 200, resp.text

    after = client.get(f"/api/v1/assets/{ip}").json()
    assert after["counts"]["resolved"] >= 1
    assert sum(after["counts"].values()) == len(after["findings"])

    matching = [f for f in after["findings"] if f["id"] == target["id"]]
    assert matching, "the triaged finding should still be listed on its host"
    assert matching[0]["status"] == "resolved"
    assert matching[0]["triage_note"] == "patched"
    # Both endpoints must agree on which scan raised it, because triage is
    # scoped to that scan.
    assert matching[0]["scan_id"] == target["scan_id"]


def test_asset_services_are_merged_without_duplicates(client):
    """Uploading the same scan twice must not duplicate its services."""
    _upload(client)
    _upload(client)
    ip = client.get("/api/v1/assets").json()[0]["ip"]
    body = client.get(f"/api/v1/assets/{ip}").json()

    pairs = [(s["port"], s["protocol"]) for s in body["asset"]["services"]]
    assert pairs, "the fixture's host has at least one service"
    assert len(pairs) == len(set(pairs)), f"duplicated services after merging: {pairs}"
    assert len(body["scans"]) >= 2, "both uploads should be attributed to this host"


def test_first_seen_is_older_than_last_seen(client):
    _upload(client)
    _upload(client)
    ip = client.get("/api/v1/assets").json()[0]["ip"]
    body = client.get(f"/api/v1/assets/{ip}").json()

    assert body["first_seen"] <= body["last_seen"]
    # Newest scan first, matching every other list in the API.
    created = [s["created_at"] for s in body["scans"]]
    assert created == sorted(created, reverse=True)


def _record(scan_id: str, **asset_fields) -> ScanRecord:
    """An in-memory scan carrying one asset, for exercising the merge directly.

    The fixture cannot reach these branches: re-uploading it produces
    identical evidence, so nothing is ever added that the first scan lacked.
    """
    evidence = SecurityEvidence(source="nmap", evidence_type="scan", assets=[Asset(**asset_fields)])
    return ScanRecord(id=scan_id, evidence_json=evidence.model_dump_json())


def test_scan_views_union_details_from_every_scan():
    """Merging is additive in both directions: fields and services."""
    # Newest first, which is the order pipeline.list_scans() guarantees.
    newer = _record("s-new", ip="10.0.0.1", services=[{"port": 22, "protocol": "tcp"}])
    older = _record(
        "s-old",
        ip="10.0.0.1",
        hostname="web01",
        os="Linux",
        services=[{"port": 22, "protocol": "tcp"}, {"port": 443, "protocol": "tcp"}],
    )

    merged, observed_by = _scan_views([newer, older])
    asset = merged["10.0.0.1"]

    # A port the newer scan no longer reports must not disappear, and one
    # already known must not be duplicated.
    assert [(s["port"], s["protocol"]) for s in asset["services"]] == [(22, "tcp"), (443, "tcp")]
    # Details the newer scan was missing are filled in from the older one.
    assert asset["hostname"] == "web01"
    assert asset["os"] == "Linux"
    # And both scans remain attributable to the host.
    assert observed_by["10.0.0.1"] == {"s-new", "s-old"}
