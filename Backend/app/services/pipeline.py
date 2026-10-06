from datetime import UTC, datetime
from uuid import uuid4

from app.db import ReportRecord, ScanRecord, SessionLocal, dumps, loads
from app.models import Finding, SecurityEvidence
from app.parsers.nmap import NmapParser
from app.services import engine
from app.services.ai.analyst import analyze_security_posture


def ingest_nmap(payload: bytes, filename: str | None) -> ScanRecord:
    parser = NmapParser()
    evidence = parser.parse_bytes(payload)
    record = ScanRecord(
        id=str(uuid4()),
        source="nmap",
        filename=filename,
        status="ingested",
        evidence_json=dumps(evidence.model_dump(mode="json")),
        asset_count=len(evidence.assets),
        findings_json="[]",
    )
    with SessionLocal() as session:
        session.add(record)
        session.commit()
    return record


def get_scan(scan_id: str) -> ScanRecord | None:
    with SessionLocal() as session:
        return session.get(ScanRecord, scan_id)


def latest_scan() -> ScanRecord | None:
    with SessionLocal() as session:
        from sqlalchemy import select

        return session.execute(select(ScanRecord).order_by(ScanRecord.created_at.desc())).scalars().first()


def run_analysis(scan_id: str) -> ScanRecord | None:
    record = get_scan(scan_id)
    if record is None:
        return None
    evidence = SecurityEvidence.model_validate(loads(record.evidence_json))
    findings = engine.analyze(evidence)
    assets = engine.normalization.normalize_evidence(evidence).assets
    ai = analyze_security_posture(assets, findings)

    for f in findings:
        f.ai_analysis = ai.model_dump()

    record.findings_json = dumps([f.model_dump(mode="json") for f in findings])
    record.analysis_json = dumps(ai.model_dump())
    record.finding_count = len(findings)
    record.status = "completed"
    with SessionLocal() as session:
        merged = session.get(ScanRecord, scan_id)
        merged.findings_json = record.findings_json
        merged.analysis_json = record.analysis_json
        merged.finding_count = record.finding_count
        merged.status = record.status
        session.commit()
    return record


def list_scans() -> list[ScanRecord]:
    from sqlalchemy import select

    with SessionLocal() as session:
        return list(session.execute(select(ScanRecord).order_by(ScanRecord.created_at.desc())).scalars())


def findings_for_scan(record: ScanRecord) -> list[Finding]:
    return [Finding.model_validate(f) for f in loads(record.findings_json)]


def create_report(scan_id: str) -> ReportRecord | None:
    record = get_scan(scan_id)
    if record is None:
        return None
    findings = findings_for_scan(record)
    analysis = loads(record.analysis_json) if record.analysis_json else {}

    lines = [
        "# Sentinel-AI Security Report",
        "",
        f"- Scan: {record.id}",
        f"- Source: {record.source}",
        f"- Generated: {datetime.now(UTC).isoformat()}",
        f"- Assets: {record.asset_count}",
        f"- Findings: {record.finding_count}",
        "",
        "## AI Summary",
        "",
        analysis.get("summary", "No AI analysis available."),
        "",
        "## Risk Assessment",
        "",
        analysis.get("risk_assessment", ""),
        "",
        "## Findings",
        "",
    ]
    for f in findings:
        lines.append(f"### {f.title} ({f.severity.value}, risk {f.risk_score})")
        lines.append("")
        lines.append(f"- Asset: {f.asset.ip if f.asset else 'unknown'}")
        lines.append(f"- Confidence: {f.confidence.value}")
        lines.append(f"- Rationale: {f.rationale}")
        lines.append(f"- Remediation: {f.remediation}")
        lines.append("")

    report = ReportRecord(id=str(uuid4()), scan_id=scan_id, content="\n".join(lines))
    with SessionLocal() as session:
        session.add(report)
        session.commit()
    return report


def get_report(report_id: str) -> ReportRecord | None:
    with SessionLocal() as session:
        return session.get(ReportRecord, report_id)
