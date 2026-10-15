from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import analysis, assets, evidence, findings, reports
from app.core.config import settings
from app.db import check_database, init_db
from app.services.ai.analyst import active_provider


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="AI-powered cybersecurity analysis platform",
    version=settings.version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    # Must stay False when origins is a wildcard; see Settings.cors_allow_credentials.
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(evidence.router)
app.include_router(analysis.router)
app.include_router(assets.router)
app.include_router(findings.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {"name": settings.app_name, "status": "running", "version": settings.version}


@app.get("/health", tags=["health"], include_in_schema=False)
@app.get("/api/v1/health", tags=["health"])
def health():
    return {
        "status": "healthy",
        "version": settings.version,
        "database": check_database(),
        "nvd_enabled": settings.nvd_enabled,
        "llm_provider": active_provider(),
        "cors_origins": settings.cors_origins,
    }