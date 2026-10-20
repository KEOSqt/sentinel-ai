# Development

## Layout

```
Backend/
  app/
    api/routes/     # FastAPI routers (evidence, analysis, assets, findings, reports)
    core/           # settings (pydantic-settings, SENTINEL_* env vars)
    db/             # SQLAlchemy engine + models (scans, reports)
    models/         # pydantic domain models
    parsers/        # Nmap XML parser
    services/       # normalization, correlation, risk, engine, pipeline
    services/vulns/ # local CVE dataset, NVD client, lookup facade
    services/ai/    # analyst (structured LLM output), rag, knowledge docs
  tests/            # pytest: parser, engine, API pipeline; fixtures/sample_nmap.xml
frontend/
  src/app/          # Next.js app router pages (overview, assets, findings, scan, reports)
                    # + error.tsx / global-error.tsx / loading.tsx / not-found.tsx boundaries
  src/components/   # interactive client components (ApiErrorState, ReportsPanel,
                  # FindingTriage)
  src/lib/          # api client + server-safe shared UI primitives
```

## Commands

| Task | Command |
| --- | --- |
| Install backend deps | `cd Backend && .venv\Scripts\python.exe -m pip install -r requirements-dev.txt` |
| Run backend | `cd Backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload` |
| Run frontend | `cd frontend && npm run dev` |
| Tests | `cd Backend && .venv\Scripts\python.exe -m pytest -q` |
| Coverage | `cd Backend && .venv\Scripts\python.exe -m pytest -q --cov=app --cov-report=term-missing` |
| Lint backend | `cd Backend && .venv\Scripts\ruff.exe check app tests` |
| Typecheck frontend | `cd frontend && npm run build` |
| Lint frontend | `cd frontend && npm run lint` |
| Full stack | `docker compose up --build` |

`requirements.txt` holds runtime dependencies; `requirements-dev.txt` layers
`ruff` and `pytest-cov` on top for local development and CI.

## Adding a Correlation Rule

Create a class extending `Rule` in `app/services/correlation.py` implementing
`evaluate(asset, vulns_by_service) -> list[Finding]`, then append an instance to `RULES`.
Cover it with a unit test in `tests/`.

Note that `app/services/triage.py` derives a finding's identity from its title,
asset ip and service. Changing how a rule sets those fields changes its
fingerprint, which would orphan any triage an analyst has recorded against it.

## Adding Knowledge for RAG

Drop `.md`/`.txt` files into `Backend/app/services/ai/knowledge/`; the retriever chunks
and scores them automatically.

## Notes

- Tests set `SENTINEL_DATABASE_URL=sqlite:///./test.db` and `SENTINEL_NVD_ENABLED=false` for determinism. That happens in `tests/conftest.py`, which pytest imports before any test module — `app` builds its settings at import time, so the env vars must be in place first.
- The AI analyst falls back to deterministic structured output when no LLM provider is reachable.

## Frontend Data Fetching

`apiGet` / `apiPost` in `src/lib/api.ts` **never throw and never return `null`**. They
resolve to `ApiResult<T>`:

```ts
const result = await apiGet<Finding[]>("/api/v1/findings");
if (!result.ok) return <ApiErrorState errors={[result.error]} />;
// result.data is T
```

This keeps two states that look identical in the UI but mean opposite things:

| Situation | Render |
| --- | --- |
| Backend unreachable / slow / erroring | `<ApiErrorState>` (with Retry) |
| Backend answered, no records | `<EmptyState>` |

Never collapse both into a falsy check — that is what previously made a stopped
backend look like an empty dashboard. Requests abort after 10s
(`REQUEST_TIMEOUT_MS`) so a hung backend surfaces as an error instead of an
indefinite load.

`src/app/error.tsx` and `global-error.tsx` catch *unexpected render* failures.
Both are Client Components, per the Next.js file conventions.
