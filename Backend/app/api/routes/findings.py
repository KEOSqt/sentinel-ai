from fastapi import APIRouter, HTTPException

from app.services import pipeline

router = APIRouter(prefix="/api/v1/findings", tags=["findings"])


@router.get("")
def list_findings():
    findings = []
    for scan in pipeline.list_scans():
        findings.extend(pipeline.loads(scan.findings_json))
    findings.sort(key=lambda f: f.get("risk_score", 0), reverse=True)
    return findings


@router.get("/{finding_id}")
def get_finding(finding_id: str):
    for scan in pipeline.list_scans():
        for finding in pipeline.loads(scan.findings_json):
            if finding.get("id") == finding_id:
                return finding
    raise HTTPException(status_code=404, detail="Finding not found")
