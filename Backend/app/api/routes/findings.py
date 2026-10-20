from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models import FindingStatus
from app.services import findings as finding_service

router = APIRouter(prefix="/api/v1/findings", tags=["findings"])


class FindingUpdate(BaseModel):
    status: FindingStatus
    note: str = Field(default="", max_length=2000)


@router.get("")
def list_findings(status: FindingStatus | None = None, scan_id: str | None = None):
    return finding_service.list_findings(
        status=status.value if status is not None else None,
        scan_id=scan_id,
    )


@router.get("/{finding_id}")
def get_finding(finding_id: str):
    finding = finding_service.get_finding(finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.patch("/{finding_id}")
def update_finding(finding_id: str, update: FindingUpdate):
    """Acknowledge or resolve a finding.

    Triage is keyed on a content fingerprint rather than the finding id, so
    the decision survives re-analysing the same scan.
    """
    updated = finding_service.update_finding(finding_id, update.status.value, update.note)
    if updated is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return updated
