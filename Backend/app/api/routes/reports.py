from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.time import to_iso_utc
from app.services import pipeline

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


class ReportRequest(BaseModel):
    scan_id: str


def _serialize(report) -> dict:
    return {
        "id": report.id,
        "scan_id": report.scan_id,
        "created_at": to_iso_utc(report.created_at),
        "content": report.content,
    }


@router.get("")
def list_reports(scan_id: str | None = None):
    # Declared before /{report_id} so the literal path is not captured as an id.
    return [
        {
            "id": r.id,
            "scan_id": r.scan_id,
            "created_at": to_iso_utc(r.created_at),
        }
        for r in pipeline.list_reports(scan_id)
    ]


@router.post("")
def create_report(request: ReportRequest):
    scan = pipeline.get_scan(request.scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status != "completed":
        raise HTTPException(status_code=409, detail="Scan has not been analysed yet")
    report = pipeline.create_report(request.scan_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return _serialize(report)


@router.get("/{report_id}")
def get_report(report_id: str):
    report = pipeline.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return _serialize(report)


@router.delete("/{report_id}")
def delete_report_route(report_id: str):
    if not pipeline.delete_report(report_id):
        raise HTTPException(status_code=404, detail="Report not found")
    return {"detail": "Report deleted"}