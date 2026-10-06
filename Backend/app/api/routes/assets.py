from fastapi import APIRouter

from app.models import SecurityEvidence
from app.services import pipeline

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.get("")
def list_assets():
    seen: dict[str, dict] = {}
    for scan in pipeline.list_scans():
        evidence = SecurityEvidence.model_validate(pipeline.loads(scan.evidence_json))
        for asset in evidence.assets:
            existing = seen.get(asset.ip)
            if existing is None:
                seen[asset.ip] = asset.model_dump(mode="json")
            else:
                for service in asset.model_dump(mode="json")["services"]:
                    if not any(s["port"] == service["port"] and s["protocol"] == service["protocol"] for s in existing["services"]):
                        existing["services"].append(service)
                if not existing.get("hostname") and asset.hostname:
                    existing["hostname"] = asset.hostname
                if not existing.get("os") and asset.os:
                    existing["os"] = asset.os
    return list(seen.values())
