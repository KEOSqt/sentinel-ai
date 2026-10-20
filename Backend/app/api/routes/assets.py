from fastapi import APIRouter, HTTPException

from app.db import ScanRecord
from app.models import SecurityEvidence
from app.services import findings as finding_service
from app.services import pipeline, triage

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


def _scan_views(scans: list[ScanRecord]) -> tuple[dict[str, dict], dict[str, set[str]]]:
    """Merge assets across scans, and record which scans observed each IP.

    Both callers need the two views and building either means parsing every
    scan's evidence, so they are produced in the same pass.

    The merged asset keeps the first version of each field it sees and only
    ever grows: services are added if a later scan saw more, and a missing
    hostname or OS is filled in. Nothing is ever removed, because a host
    whose second scan stopped reporting a port did not lose the port.
    """
    merged: dict[str, dict] = {}
    observed_by: dict[str, set[str]] = {}

    for scan in scans:
        evidence = SecurityEvidence.model_validate(pipeline.loads(scan.evidence_json))
        for asset in evidence.assets:
            observed_by.setdefault(asset.ip, set()).add(scan.id)
            payload = asset.model_dump(mode="json")
            existing = merged.get(asset.ip)
            if existing is None:
                merged[asset.ip] = payload
                continue
            for service in payload["services"]:
                if not any(s["port"] == service["port"] and s["protocol"] == service["protocol"] for s in existing["services"]):
                    existing["services"].append(service)
            if not existing.get("hostname") and asset.hostname:
                existing["hostname"] = asset.hostname
            if not existing.get("os") and asset.os:
                existing["os"] = asset.os

    return merged, observed_by


def _scan_summary(scan: ScanRecord) -> dict:
    return {
        "id": scan.id,
        "source": scan.source,
        "filename": scan.filename,
        "status": scan.status,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "asset_count": scan.asset_count,
        "finding_count": scan.finding_count,
    }


@router.get("")
def list_assets():
    merged, _ = _scan_views(pipeline.list_scans())
    return list(merged.values())


@router.get("/{ip}")
def get_asset(ip: str):
    """One host: how it was seen, what was found on it, and its triage state.

    The list endpoint can answer "which hosts exist" but not "what do we know
    about this one", because the answer is spread across the merged evidence,
    every scan that observed it, and the triage rows on its findings.
    """
    scans = pipeline.list_scans()
    merged, observed_by = _scan_views(scans)
    asset = merged.get(ip)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    observed = observed_by.get(ip, set())
    ordered = sorted((s for s in scans if s.id in observed), key=lambda s: s.created_at)  # oldest first

    # Findings name their asset by IP, so this is every finding raised against
    # this host in any scan, already carrying its triage status.
    asset_findings = [
        finding
        for finding in finding_service.list_findings()
        if (finding.get("asset") or {}).get("ip") == ip
    ]

    counts = {triage.DEFAULT_STATUS: 0, "acknowledged": 0, "resolved": 0}
    for finding in asset_findings:
        counts[finding["status"]] = counts.get(finding["status"], 0) + 1

    return {
        "asset": asset,
        "first_seen": ordered[0].created_at.isoformat() if ordered else None,
        "last_seen": ordered[-1].created_at.isoformat() if ordered else None,
        "scans": [_scan_summary(s) for s in reversed(ordered)],  # newest first, like every other list
        "findings": asset_findings,
        "counts": counts,
    }
