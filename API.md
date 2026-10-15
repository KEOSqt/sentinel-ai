# API Reference

Base URL: `http://localhost:8000`. Interactive docs at `/docs`.

## Health

### GET /api/v1/health
Also served (as an alias) at `GET /health`.

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": true,
  "nvd_enabled": true,
  "llm_provider": "ollama",
  "cors_origins": ["http://localhost:3000"]
}
```

`llm_provider` reports the provider the analyst will actually try first, which
is `openai` when `SENTINEL_OPENAI_API_KEY` is set and `ollama` otherwise.
(`SENTINEL_ANTHROPIC_API_KEY` is accepted by the settings layer but is currently
unused by the analyst.)

## CORS

Origins are configured with `SENTINEL_CORS_ORIGINS` as a JSON list. Credentialed
requests are enabled automatically, except when the list contains `*` — the CORS
spec forbids pairing a wildcard origin with credentials, and browsers reject it.

## Ingest evidence

### POST /api/v1/evidence/nmap
Multipart upload of an Nmap XML file (max 10 MB).

Response 200:
```json
{
  "scan_id": "uuid",
  "status": "ingested",
  "asset_count": 2,
  "assets": [ { "ip": "...", "hostname": "...", "os": "...", "services": [] } ]
}
```
Errors: `413` file too large, `422` invalid/unsafe XML.

## Analyze

### POST /api/v1/analyze
```json
{ "scan_id": "uuid | null" }
```
If `scan_id` is omitted, the most recent scan is analyzed.

Response 200:
```json
{
  "scan_id": "...",
  "status": "completed",
  "asset_count": 2,
  "finding_count": 10,
  "analysis": { "summary": "...", "risk_assessment": "...", "priority_findings": [], "attack_paths": [], "recommendations": [], "missing_information": [] },
  "findings": []
}
```
Errors: `404` no scans / scan not found.

### GET /api/v1/scans
List recent scans: `id`, `source`, `filename`, `status`, `created_at`, `asset_count`, `finding_count`.

## Assets

### GET /api/v1/assets
Deduplicated assets aggregated across scans: `ip`, `hostname`, `os`, `services[]`, `exposure`, `metadata`.

## Findings

### GET /api/v1/findings
All findings across scans, sorted by risk score descending. The AI analysis is
**not** included here; it belongs to the scan, not to each finding.

### GET /api/v1/findings/{id}
Single finding with `title`, `description`, `severity`, `risk_score`, `confidence`, `asset`, `affected_service`, `evidence[]`, `rationale`, `remediation`, `references[]`, `status`, `ai_analysis`.

`ai_analysis` here is the scan-level analysis, attached on read (`null` if the
scan has not been analyzed).

## Reports

### GET /api/v1/reports
Lists reports newest first. Optional `?scan_id=` filter.

```json
[ { "id": "...", "scan_id": "...", "created_at": "..." } ]
```

Metadata only — the markdown body is omitted because it dominates the payload.

### POST /api/v1/reports
```json
{ "scan_id": "..." }
```
Creates a markdown security report; returns `{ id, scan_id, created_at, content }`.

### GET /api/v1/reports/{id}
Returns the stored report.
