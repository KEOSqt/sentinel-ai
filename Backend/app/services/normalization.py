from app.models import Asset, SecurityEvidence


def normalize_evidence(evidence: SecurityEvidence) -> SecurityEvidence:
    """Deduplicate assets by IP and merge their services/metadata."""
    by_ip: dict[str, Asset] = {}

    for asset in evidence.assets:
        key = asset.ip.strip().lower()
        existing = by_ip.get(key)
        if existing is None:
            by_ip[key] = asset.model_copy(deep=True)
            continue

        if not existing.hostname and asset.hostname:
            existing.hostname = asset.hostname
        if not existing.os and asset.os:
            existing.os = asset.os
        if asset.exposure != "unknown" and existing.exposure == "unknown":
            existing.exposure = asset.exposure

        seen = {(s.port, s.protocol) for s in existing.services}
        for svc in asset.services:
            if (svc.port, svc.protocol) not in seen:
                existing.services.append(svc)
                seen.add((svc.port, svc.protocol))

        existing.metadata.update(asset.metadata)

    return SecurityEvidence(
        id=evidence.id,
        source=evidence.source,
        evidence_type=evidence.evidence_type,
        timestamp=evidence.timestamp,
        assets=list(by_ip.values()),
        metadata=evidence.metadata,
    )
