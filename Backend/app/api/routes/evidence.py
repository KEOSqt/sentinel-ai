from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.models import SecurityEvidence
from app.parsers.nmap import NmapParseError
from app.services import pipeline

router = APIRouter(prefix="/api/v1/evidence", tags=["evidence"])


@router.post("/nmap")
async def upload_nmap(file: UploadFile = File(...)):
    payload = await file.read()
    if len(payload) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File too large")
    try:
        record = pipeline.ingest_nmap(payload, file.filename)
    except NmapParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    evidence = SecurityEvidence.model_validate(pipeline.loads(record.evidence_json))
    return {
        "scan_id": record.id,
        "status": record.status,
        "asset_count": record.asset_count,
        "assets": [a.model_dump(mode="json") for a in evidence.assets],
    }
