from pydantic import BaseModel
from typing import List, Optional


class Service(BaseModel):
    port: int
    protocol: str
    service: str
    version: Optional[str] = None


class Asset(BaseModel):
    ip: str
    hostname: Optional[str] = None
    os: Optional[str] = None
    services: List[Service] = []


class SecurityEvidence(BaseModel):
    assets: List[Asset] = []