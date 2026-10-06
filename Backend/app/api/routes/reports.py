from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import pipeline

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


class ReportRequest(BaseModel):
    scan_id: str


@router.post("")
def create_report(request: ReportRequest):
    report = pipeline.create_report(request.scan_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"id": report.id, "scan_id": report.scan_id, "created_at": report.created_at.isoformat(), "content": report.content}


@router.get("/{report_id}")
def get_report(report_id: str):
    report = pipeline.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"id": report.id, "scan_id": report.scan_id, "created_at": report.created_at.isoformat(), "content": report.content}
