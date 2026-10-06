from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Service(BaseModel):
    port: int
    protocol: str = "tcp"
    service: str = "unknown"
    product: Optional[str] = None
    version: Optional[str] = None
    state: str = "open"


class Asset(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    ip: str
    hostname: Optional[str] = None
    os: Optional[str] = None
    services: list[Service] = Field(default_factory=list)
    exposure: str = "unknown"
    metadata: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    source: str = "unknown"
    evidence_type: str = "unknown"
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class SecurityEvidence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str = "unknown"
    evidence_type: str = "unknown"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assets: list[Asset] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Confidence(str, Enum):
    CONFIRMED = "confirmed"
    PROBABLE = "probable"
    POSSIBLE = "possible"
    UNKNOWN = "unknown"


class Vulnerability(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    severity: Severity = Severity.MEDIUM
    cvss: Optional[float] = None
    confidence: Confidence = Confidence.UNKNOWN
    references: list[str] = Field(default_factory=list)


class FindingStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str = ""
    severity: Severity = Severity.MEDIUM
    risk_score: float = 0.0
    confidence: Confidence = Confidence.UNKNOWN
    asset: Optional[Asset] = None
    affected_service: Optional[Service] = None
    evidence: list[Evidence] = Field(default_factory=list)
    rationale: str = ""
    remediation: str = ""
    references: list[str] = Field(default_factory=list)
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    status: FindingStatus = FindingStatus.OPEN
    ai_analysis: Optional[dict[str, Any]] = None
