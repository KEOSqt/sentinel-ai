from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models import FindingStatus
from app.services import pipeline, triage

router = APIRouter(prefix="/api/v1/findings", tags=["findings"])


class FindingUpdate(BaseModel):
    status: FindingStatus
    note: str = Field(default="", max_length=2000)


def _collect() -> list[tuple[str, dict]]:
    """Every finding across scans, paired with its scan id.

    Findings live inside each scan's JSON blob, so a finding id alone does not
    say which scan it belongs to.
    """
    out: list[tuple[str, dict]] = []
    for scan in pipeline.list_scans():
        for finding in pipeline.loads(scan.findings_json):
            out.append((scan.id, finding))
    return out


def _decorate(scan_id: str, finding: dict, triaged: dict) -> dict:
    """Overlay stored triage onto the stored finding."""
    enriched = dict(finding)
    enriched["scan_id"] = scan_id
    enriched["status"] = triaged.get("status", triage.DEFAULT_STATUS)
    enriched["triage_note"] = triaged.get("note", "")
    enriched["triaged_at"] = triaged.get("updated_at")
    return enriched


@router.get("")
def list_findings(status: FindingStatus | None = None, scan_id: str | None = None):
    findings: list[dict] = []
    for scan in pipeline.list_scans():
        if scan_id is not None and scan.id != scan_id:
            continue
        stored = pipeline.loads(scan.findings_json)
        triaged = triage.triage_map(scan.id, stored)
        for finding in stored:
            # The analysis lives on the scan, not on each finding. Older scans
            # may still carry a per-finding copy; drop it so the list payload
            # stays small.
            finding.pop("ai_analysis", None)
            findings.append(_decorate(scan.id, finding, triaged.get(triage.finding_key(scan.id, finding), {})))

    if status is not None:
        findings = [f for f in findings if f["status"] == status.value]

    findings.sort(key=lambda f: f.get("risk_score", 0), reverse=True)
    return findings


@router.get("/{finding_id}")
def get_finding(finding_id: str):
    for scan_id, finding in _collect():
        if finding.get("id") != finding_id:
            continue
        enriched = _decorate(scan_id, finding, triage.triage_for(scan_id, finding))
        # Re-attach the scan-level analysis so the detail response keeps
        # its documented shape without storing it N times.
        record = pipeline.get_scan(scan_id)
        enriched["ai_analysis"] = pipeline.loads(record.analysis_json) if record and record.analysis_json else None
        return enriched
    raise HTTPException(status_code=404, detail="Finding not found")


@router.patch("/{finding_id}")
def update_finding(finding_id: str, update: FindingUpdate):
    """Acknowledge or resolve a finding.

    Triage is keyed on a content fingerprint rather than the finding id, so the
    decision survives re-analysing the same scan.
    """
    for scan_id, finding in _collect():
        if finding.get("id") == finding_id:
            stored = triage.set_triage(scan_id, finding, update.status.value, update.note)
            return _decorate(scan_id, finding, stored)
    raise HTTPException(status_code=404, detail="Finding not found")