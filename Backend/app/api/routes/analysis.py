from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models import SecurityEvidence
from app.services import findings as finding_service
from app.services import pipeline

router = APIRouter(prefix="/api/v1", tags=["analysis"])


class AnalyzeRequest(BaseModel):
    scan_id: str | None = None


@router.post("/analyze")
def analyze(request: AnalyzeRequest):
    scan_id = request.scan_id
    if scan_id is None:
        latest = pipeline.latest_scan()
        if latest is None:
            raise HTTPException(status_code=404, detail="No scans available")
        scan_id = latest.id

    record = pipeline.run_analysis(scan_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    return {
        "scan_id": record.id,
        "status": record.status,
        "asset_count": record.asset_count,
        "finding_count": record.finding_count,
        "analysis": pipeline.loads(record.analysis_json) if record.analysis_json else None,
        "findings": pipeline.loads(record.findings_json),
    }


@router.get("/scans")
def list_scans():
    return [pipeline.scan_summary(s) for s in pipeline.list_scans()]


@router.get("/scans/{scan_id}")
def get_scan(scan_id: str):
    """One scan: the evidence it ingested, the findings it produced, and the AI analysis.

    A scan is what the whole pipeline produces, but the list endpoint can only
    show counts. This is the endpoint that answers "what did this scan actually
    see, what did it raise, and what did the analyst make of it" — including for
    a scan that has been uploaded but not yet analysed, which still has assets
    and no findings.
    """
    record = pipeline.get_scan(scan_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    evidence = SecurityEvidence.model_validate(pipeline.loads(record.evidence_json))
    scan_findings = finding_service.list_findings(scan_id=scan_id)

    return {
        "scan": pipeline.scan_summary(record),
        "analysis": pipeline.loads(record.analysis_json) if record.analysis_json else None,
        # This scan's own evidence, not the cross-scan merged view the assets
        # endpoint serves: provenance is the point of this payload.
        "assets": [asset.model_dump(mode="json") for asset in evidence.assets],
        "findings": scan_findings,
        "counts": finding_service.count_by_status(scan_findings),
    }
