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

Origins are configured with `SENTINEL_CORS_ORIGINS`. Both of these work:

```
SENTINEL_CORS_ORIGINS=["http://localhost:3000","http://example.com"]   # JSON array
SENTINEL_CORS_ORIGINS=http://localhost:3000,http://example.com        # comma-separated
```

Credentialed requests are enabled automatically, except when the list contains
`*` — the CORS spec forbids pairing a wildcard origin with credentials, and
browsers reject it. A malformed value is rejected at startup with a message
showing the accepted formats.

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

### GET /api/v1/assets/{ip}
One host, assembled from everything that is known about it. This is the
merged asset plus the provenance and findings that the list endpoint cannot
carry:

| Field | Meaning |
| --- | --- |
| `asset` | The merged asset (same shape as the list, plus everything later scans added) |
| `scans[]` | Every scan that observed this host, newest first: `id`, `source`, `filename`, `status`, `created_at`, `asset_count`, `finding_count` |
| `first_seen` / `last_seen` | `created_at` of the oldest and newest of those scans |
| `findings[]` | Every finding raised against this host in any scan, with triage (`status`, `triage_note`, `scan_id`) — same shape as `GET /api/v1/findings` |
| `counts` | How many of those findings are `open`, `acknowledged` and `resolved` |

Errors: `404` no scan has ever reported this address.

Merging is additive: a service or hostname seen once is never dropped because
a later scan stopped reporting it, and a duplicate port/protocol pair is not
added twice. Triage is scoped per scan, so the same title raised by two scans
appears twice and can be triaged independently — `scans[]` and each finding's
`scan_id` say which is which.

## Findings

### GET /api/v1/findings
All findings across scans, sorted by risk score descending. The AI analysis is
**not** included here; it belongs to the scan, not to each finding.

Optional query parameters:

| Parameter | Example | Effect |
| --- | --- | --- |
| `status` | `?status=acknowledged` | Only findings with that triage status |
| `scan_id` | `?scan_id=<uuid>` | Only findings from that scan |

Each finding carries `scan_id`, `status`, `triage_note` and `triaged_at`.

### GET /api/v1/findings/{id}
Single finding with `title`, `description`, `severity`, `risk_score`, `confidence`, `asset`, `affected_service`, `evidence[]`, `rationale`, `remediation`, `references[]`, `status`, `triage_note`, `triaged_at`, `ai_analysis`.

`ai_analysis` here is the scan-level analysis, attached on read (`null` if the
scan has not been analyzed).

### PATCH /api/v1/findings/{id}
Record an analyst decision about a finding.

```json
{ "status": "acknowledged", "note": "Tracked in TICKET-42" }
```

`status` must be `open`, `acknowledged` or `resolved` (anything else is
rejected with `422`). `note` is optional, defaults to `""`, max 2000 characters.
Returns the updated finding. Errors: `404` finding not found.

**Triage survives re-analysis.** Findings are regenerated with new UUIDs every
time a scan is analysed, so status is keyed on a content fingerprint (scan id,
title, asset ip, service port and protocol) rather than the finding id.
Re-analysing the same scan therefore keeps every acknowledgement.

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
