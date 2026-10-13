from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
    return [
        {
            "id": s.id,
            "source": s.source,
            "filename": s.filename,
            "status": s.status,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "asset_count": s.asset_count,
            "finding_count": s.finding_count,
        }
        for s in pipeline.list_scans()
    ]
