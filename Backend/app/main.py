from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import init_db

app = FastAPI(
    title=settings.app_name,
    description="AI-powered cybersecurity analysis platform",
    version=settings.version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def root():
    return {"name": settings.app_name, "status": "running", "version": settings.version}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/v1/health")
def health_v1():
    return {"status": "healthy"}
