# Development

## Layout

```
Backend/
  app/
    api/routes/     # FastAPI routers (evidence, analysis, assets, findings, reports)
    core/           # settings (pydantic-settings, SENTINEL_* env vars), UTC helpers
    db/             # SQLAlchemy engine + models (scans, reports, triage)
    models/         # pydantic domain models
    parsers/        # Nmap XML parser
    services/       # normalization, correlation, risk, engine, pipeline
    services/vulns/ # local CVE dataset, NVD client, lookup facade
    services/ai/    # analyst (structured LLM output), rag, knowledge docs
  tests/            # pytest: parser, engine, API pipeline, AI/NVD/UTC; sample_nmap.xml
frontend/
  src/app/          # Next.js app router pages (overview, assets, findings, scans,
                    # scan upload, reports) + error/loading/not-found boundaries
  src/components/   # interactive client components (ApiErrorState, ReportsPanel,
                    # FindingTriage)
  src/lib/          # api client, retry hook, markdown renderer, shared primitives
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
| Tests frontend | `cd frontend && npm test` |
| Typecheck frontend | `cd frontend && npm run build` |
| Lint frontend | `cd frontend && npm run lint` |
| Full stack | `docker compose up --build` |

`requirements.txt` holds runtime dependencies; `requirements-dev.txt` layers
`pytest`, `pytest-cov` and `ruff` on top for local development and CI.

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

- Tests set an absolute `SENTINEL_DATABASE_URL` (so the working directory does not matter), `SENTINEL_NVD_ENABLED=false` and `SENTINEL_LLM_PROVIDER=none`, and clear provider keys for determinism. That happens in `tests/conftest.py`, which pytest imports before any test module — `app` builds its settings at import time, so the env vars must be in place first.
- The AI analyst falls back to deterministic structured output when no LLM provider is reachable. NVD lookups are cached (default 15 minutes) and spaced (default 6 seconds) to stay within the public rate limit.

## Frontend Data Fetching

`apiGet` / `apiPost` / `apiUpload` / `apiDelete` in `src/lib/api.ts` **never throw
and never return `null`**. They resolve to `ApiResult<T>`:

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

Pages use the `useRetry` hook (`src/lib/use-retry.ts`): the returned `attempt`
is an effect dependency, and the Retry button resets loading/error state before
incrementing it. Avoid calling `setState` synchronously inside an effect body —
the React lint rules reject it and it causes cascading renders.

`src/app/error.tsx` and `global-error.tsx` catch *unexpected render* failures.
Both are Client Components, per the Next.js file conventions.
