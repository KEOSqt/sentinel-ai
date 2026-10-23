import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Float, Integer, String, Text, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


class ScanRecord(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    source: Mapped[str] = mapped_column(String, default="nmap")
    filename: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    evidence_json: Mapped[str] = mapped_column(Text, default="{}")
    findings_json: Mapped[str] = mapped_column(Text, default="[]")
    analysis_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset_count: Mapped[int] = mapped_column(Integer, default=0)
    finding_count: Mapped[int] = mapped_column(Integer, default=0)


class ReportRecord(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scan_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    content: Mapped[str] = mapped_column(Text, default="")


class FindingTriageRecord(Base):
    """Analyst decisions about a finding, keyed by a content fingerprint.

    Not keyed by Finding.id: those are fresh UUIDs on every re-analysis, so an
    id-keyed row would be orphaned — silently discarding every status the
    moment someone re-runs the analysis. See app.services.triage.finding_key.
    """

    __tablename__ = "finding_triage"

    finding_key: Mapped[str] = mapped_column(String, primary_key=True)
    scan_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="open")
    note: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class FindingRecord(Base):
    """Findings stored in their own table so they can be queried by id
    without walking every scan's JSON blob.

    Stored redundantly with findings_json on ScanRecord for backward
    compatibility during the transition; new code reads from this table.
    """

    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scan_id: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[str] = mapped_column(String)
    asset_ip: Mapped[str | None] = mapped_column(String, nullable=True)
    affected_service_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    affected_service_protocol: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="open")
    triage_note: Mapped[str] = mapped_column(Text, default="")
    triaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Run Alembic migrations to bring the database schema up to date.

    Replaces the old ``Base.metadata.create_all()`` approach, which silently
    fails to apply schema changes to existing databases. Alembic tracks the
    schema version in an ``alembic_version`` table and applies only the
    migrations that haven't run yet.
    """
    from alembic import command
    from alembic.config import Config
    import os

    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    alembic_ini = os.path.join(backend_dir, "alembic.ini")
    alembic_cfg = Config(alembic_ini)
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(alembic_cfg, "head")


def get_session() -> Session:
    return SessionLocal()


def check_database() -> bool:
    """True when the configured database accepts a trivial query."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


def dumps(obj: Any) -> str:
    return json.dumps(obj, default=str)


def loads(payload: str) -> Any:
    return json.loads(payload)
