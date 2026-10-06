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
  src/lib/          # api client + shared UI components
```

## Commands

| Task | Command |
| --- | --- |
| Run backend | `cd Backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload` |
| Run frontend | `cd frontend && npm run dev` |
| Tests | `cd Backend && .venv\Scripts\python.exe -m pytest -q` |
| Lint backend | `cd Backend && .venv\Scripts\ruff.exe check app tests` |
| Typecheck frontend | `cd frontend && npm run build` |
| Lint frontend | `cd frontend && npm run lint` |
| Full stack | `docker compose up --build` |

## Adding a Correlation Rule

Create a class extending `Rule` in `app/services/correlation.py` implementing
`evaluate(asset, vulns_by_service) -> list[Finding]`, then append an instance to `RULES`.
Cover it with a unit test in `tests/`.

## Adding Knowledge for RAG

Drop `.md`/`.txt` files into `Backend/app/services/ai/knowledge/`; the retriever chunks
and scores them automatically.

## Notes

- Tests set `SENTINEL_DATABASE_URL=sqlite:///./test.db` and `SENTINEL_NVD_ENABLED=false` for determinism.
- The AI analyst falls back to deterministic structured output when no LLM provider is reachable.
