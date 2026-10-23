"""Assembling findings out of scan records, with analyst triage overlaid.

Findings are stored in their own table (`findings`) for efficient querying,
and analyst triage lives in `finding_triage`, keyed by a content fingerprint
because finding UUIDs are regenerated on every re-analysis.

The findings assembly walks the `findings` table rather than every scan's
JSON, so listing and lookup are O(1) indexed queries instead of O(n*m)
walks through every scan's JSON blob.
"""

from typing import Any

from app.core.time import to_iso_utc
from app.db import FindingRecord, FindingTriageRecord, SessionLocal
from app.services import pipeline, triage
from sqlalchemy import select


def _merge(scan_id: str, finding: dict[str, Any], triaged: dict[str, Any]) -> dict[str, Any]:
    """Overlay provenance and analyst triage onto one stored finding."""
    enriched = dict(finding)
    enriched["scan_id"] = scan_id
    enriched["status"] = triaged.get("status", triage.DEFAULT_STATUS)
    enriched["triage_note"] = triaged.get("note", "")
    enriched["triaged_at"] = triaged.get("updated_at")
    return enriched


def _enrich_from_row(row: Any) -> dict[str, Any]:
    """Build a finding dict from a FindingRecord row."""
    return {
        "id": row.id,
        "title": row.title,
        "severity": row.severity,
        "risk_score": row.risk_score,
        "confidence": row.confidence,
        "asset": {"ip": row.asset_ip} if row.asset_ip else None,
        "affected_service": (
            {
                "port": row.affected_service_port,
                "protocol": row.affected_service_protocol,
            }
            if row.affected_service_port
            else None
        ),
        # Fields not stored in findings table but expected by frontend:
        "description": "",
        "rationale": "",
        "remediation": "",
        "references": [],
        "evidence": [],
        "vulnerabilities": [],
    }


def list_findings(status: str | None = None, scan_id: str | None = None) -> list[dict[str, Any]]:
    """Every finding across scans, risk score descending, with triage applied.

    `status` and `scan_id` are optional filters.
    """
    with SessionLocal() as session:
        stmt = select(FindingRecord)
        if scan_id is not None:
            stmt = stmt.where(FindingRecord.scan_id == scan_id)
        rows = session.execute(stmt).scalars().all()

    if not rows:
        return []

    # Build finding dicts and compute triage fingerprints
    findings: list[dict[str, Any]] = []
    key_to_finding: dict[str, dict[str, Any]] = {}
    key_to_scan_id: dict[str, str] = {}

    for row in rows:
        finding = _enrich_from_row(row)
        key = triage.finding_key(row.scan_id, finding)
        key_to_finding[key] = finding
        key_to_scan_id[key] = row.scan_id
        findings.append(key)

    # Batch-load triage for all findings
    with SessionLocal() as session:
        triage_rows = session.execute(
            select(FindingTriageRecord).where(
                FindingTriageRecord.finding_key.in_(list(key_to_finding.keys()))
            )
        ).scalars()
        triage_map = {
            row.finding_key: {
                "status": row.status,
                "note": row.note or "",
                "updated_at": to_iso_utc(row.updated_at),
            }
            for row in triage_rows
        }

    # Apply triage overlay
    result: list[dict[str, Any]] = []
    for key in findings:
        scan_id_val = key_to_scan_id[key]
        finding = key_to_finding[key]
        triaged = triage_map.get(
            key,
            {"status": triage.DEFAULT_STATUS, "note": "", "updated_at": None},
        )
        enriched = _merge(scan_id_val, finding, triaged)
        if status is None or enriched["status"] == status:
            result.append(enriched)

    result.sort(key=lambda f: f.get("risk_score", 0), reverse=True)
    return result


def count_by_status(findings: list[dict[str, Any]]) -> dict[str, int]:
    """How many of these findings are open, acknowledged and resolved.

    Always reports all three keys so an empty list and a fully-triaged list
    are both shaped the same for the caller.
    """
    counts = {triage.DEFAULT_STATUS: 0, "acknowledged": 0, "resolved": 0}
    for finding in findings:
        counts[finding["status"]] = counts.get(finding["status"], 0) + 1
    return counts


def get_finding(finding_id: str) -> dict[str, Any] | None:
    """One finding by id, with the scan-level analysis attached on read.

    Returns None when no scan contains that id, which is the only way for a
    finding id to be wrong: there is no findings table to point at.
    """
    with SessionLocal() as session:
        row = session.get(FindingRecord, finding_id)
    if row is None:
        return None

    finding = _enrich_from_row(row)
    triaged = triage.triage_for(row.scan_id, finding)
    enriched = _merge(row.scan_id, finding, triaged)

    record = pipeline.get_scan(row.scan_id)
    enriched["ai_analysis"] = (
        pipeline.loads(record.analysis_json) if record and record.analysis_json else None
    )
    return enriched


def update_finding(finding_id: str, status: str, note: str = "") -> dict[str, Any] | None:
    """Record an analyst decision against a finding, keyed on its fingerprint.

    Returns None when the id is unknown, so the route can turn that into a
    404 rather than silently creating a triage row nobody will ever read.
    """
    with SessionLocal() as session:
        row = session.get(FindingRecord, finding_id)
        if row is None:
            return None

        finding = _enrich_from_row(row)
        stored = triage.set_triage(row.scan_id, finding, status, note)
        return _merge(row.scan_id, finding, stored)