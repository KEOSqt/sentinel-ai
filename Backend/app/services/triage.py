"""Analyst triage of findings.

Findings are regenerated with brand-new UUIDs every time a scan is analysed,
so their ids cannot identify "the same finding" over time. Triage is therefore
keyed on a fingerprint built from the parts of a finding that stay the same
across runs: its title, the affected asset, and the affected service.
"""

import hashlib
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from app.core.time import to_iso_utc
from app.db import FindingTriageRecord, SessionLocal
from app.models import FindingStatus

DEFAULT_STATUS = FindingStatus.OPEN.value


def finding_key(scan_id: str, finding: dict[str, Any]) -> str:
    """Stable identity for a finding within a scan.

    Derived only from fields the correlation rules set deterministically, so
    re-analysing the same scan produces the same key and preserves triage.
    """
    asset = finding.get("asset") or {}
    service = finding.get("affected_service") or {}
    parts = [
        scan_id,
        str(finding.get("title", "")),
        str(asset.get("ip", "")),
        str(service.get("port", "")),
        str(service.get("protocol", "")),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]


def triage_for(scan_id: str, finding: dict[str, Any]) -> dict[str, Any]:
    """Stored triage for one finding, or the default open status."""
    key = finding_key(scan_id, finding)
    with SessionLocal() as session:
        record = session.get(FindingTriageRecord, key)
        if record is None:
            return {"status": DEFAULT_STATUS, "note": "", "updated_at": None}
        return {
            "status": record.status,
            "note": record.note or "",
            "updated_at": to_iso_utc(record.updated_at),
        }


def triage_map(scan_id: str, findings: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """All triage for one scan in a single query, keyed by fingerprint."""
    keys = {finding_key(scan_id, f): f for f in findings}
    if not keys:
        return {}
    with SessionLocal() as session:
        rows = session.execute(
            select(FindingTriageRecord).where(FindingTriageRecord.finding_key.in_(list(keys)))
        ).scalars()
        return {
            row.finding_key: {
                "status": row.status,
                "note": row.note or "",
                "updated_at": to_iso_utc(row.updated_at),
            }
            for row in rows
        }


def set_triage(scan_id: str, finding: dict[str, Any], status: str, note: str = "") -> dict[str, Any]:
    """Create or update the triage row for a finding."""
    key = finding_key(scan_id, finding)
    now = datetime.now(UTC)
    with SessionLocal() as session:
        record = session.get(FindingTriageRecord, key)
        if record is None:
            record = FindingTriageRecord(finding_key=key, scan_id=scan_id, status=status, note=note)
            session.add(record)
        else:
            record.status = status
            record.note = note
        record.updated_at = now
        session.commit()
    return {"status": status, "note": note, "updated_at": to_iso_utc(now)}