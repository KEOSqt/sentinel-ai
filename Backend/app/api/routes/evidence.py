from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.core.config import settings
from app.models import SecurityEvidence
from app.parsers.nmap import NmapParseError
from app.services import pipeline

router = APIRouter(prefix="/api/v1/evidence", tags=["evidence"])


@router.post("/nmap")
async def upload_nmap(request: Request, file: UploadFile = File(...)):
    # Pre-check Content-Length before buffering the body, so an oversized
    # upload is rejected with 413 without spending memory on it.
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            cl = int(content_length)
        except ValueError:
            cl = 0
        if cl > settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="File too large")

    # Read in chunks and enforce size limit even if Content-Length is absent
    chunks: list[bytes] = []
    size = 0
    while chunk := await file.read(1024 * 1024):
        size += len(chunk)
        if size > settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="File too large")
        chunks.append(chunk)
    payload = b"".join(chunks)

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