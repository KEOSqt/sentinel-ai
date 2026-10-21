"""Assembling findings out of scan records, with analyst triage overlaid.

Findings are stored as JSON inside each scan row rather than in their own
table, so "all findings" means walking every scan. Both the findings and the
assets routers need that walk *and* the triage overlay, so it lives here
instead of being duplicated in each router.

The triage overlay itself lives in app.services.triage; this module only
decides which stored finding to combine with which stored triage row.
"""

from typing import Any

from app.services import pipeline, triage


def _merge(scan_id: str, finding: dict[str, Any], triaged: dict[str, Any]) -> dict[str, Any]:
    """Overlay provenance and analyst triage onto one stored finding."""
    enriched = dict(finding)
    enriched["scan_id"] = scan_id
    enriched["status"] = triaged.get("status", triage.DEFAULT_STATUS)
    enriched["triage_note"] = triaged.get("note", "")
    enriched["triaged_at"] = triaged.get("updated_at")
    return enriched


def list_findings(status: str | None = None, scan_id: str | None = None) -> list[dict[str, Any]]:
    """Every finding across scans, risk score descending, with triage applied.

    `status` and `scan_id` are optional filters; both are applied while
    walking the scans so the triage rows are only read for scans that
    actually contribute.
    """
    findings: list[dict[str, Any]] = []
    for scan in pipeline.list_scans():
        if scan_id is not None and scan.id != scan_id:
            continue
        stored = pipeline.loads(scan.findings_json)
        if not stored:
            continue
        triaged = triage.triage_map(scan.id, stored)
        for finding in stored:
            # The analysis lives on the scan, not on each finding. Older scans
            # may still carry a per-finding copy; drop it so the list payload
            # stays small.
            finding.pop("ai_analysis", None)
            key = triage.finding_key(scan.id, finding)
            enriched = _merge(scan.id, finding, triaged.get(key, {}))
            if status is None or enriched["status"] == status:
                findings.append(enriched)

    findings.sort(key=lambda f: f.get("risk_score", 0), reverse=True)
    return findings


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
    for scan in pipeline.list_scans():
        for finding in pipeline.loads(scan.findings_json):
            if finding.get("id") != finding_id:
                continue
            enriched = _merge(scan.id, finding, triage.triage_for(scan.id, finding))
            record = pipeline.get_scan(scan.id)
            enriched["ai_analysis"] = pipeline.loads(record.analysis_json) if record and record.analysis_json else None
            return enriched
    return None


def update_finding(finding_id: str, status: str, note: str = "") -> dict[str, Any] | None:
    """Record an analyst decision against a finding, keyed on its fingerprint.

    Returns None when the id is unknown, so the route can turn that into a
    404 rather than silently creating a triage row nobody will ever read.
    """
    for scan in pipeline.list_scans():
        for finding in pipeline.loads(scan.findings_json):
            if finding.get("id") != finding_id:
                continue
            stored = triage.set_triage(scan.id, finding, status, note)
            return _merge(scan.id, finding, stored)
    return None
