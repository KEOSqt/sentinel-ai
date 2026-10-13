from fastapi import APIRouter, HTTPException

from app.services import pipeline

router = APIRouter(prefix="/api/v1/findings", tags=["findings"])


@router.get("")
def list_findings():
    findings = []
    for scan in pipeline.list_scans():
        for finding in pipeline.loads(scan.findings_json):
            # The analysis lives on the scan, not on each finding. Older scans
            # may still carry a per-finding copy; drop it so the list payload
            # stays small.
            finding.pop("ai_analysis", None)
            findings.append(finding)
    findings.sort(key=lambda f: f.get("risk_score", 0), reverse=True)
    return findings


@router.get("/{finding_id}")
def get_finding(finding_id: str):
    for scan in pipeline.list_scans():
        for finding in pipeline.loads(scan.findings_json):
            if finding.get("id") == finding_id:
                # Re-attach the scan-level analysis so the detail response keeps
                # its documented shape without storing it N times.
                finding["ai_analysis"] = pipeline.loads(scan.analysis_json) if scan.analysis_json else None
                return finding
    raise HTTPException(status_code=404, detail="Finding not found")