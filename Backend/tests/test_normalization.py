from app.models import Asset, SecurityEvidence, Service
from app.services.normalization import normalize_evidence


def _asset(ip: str, hostname: str | None = None, os: str | None = None,
           services: list[Service] | None = None,
           exposure: str = "unknown",
           metadata: dict | None = None) -> Asset:
    return Asset(
        ip=ip,
        hostname=hostname,
        os=os,
        services=services or [],
        exposure=exposure,
        metadata=metadata or {},
    )


def test_normalization_deduplicates_assets_by_ip():
    """Two assets with the same IP should be merged into one."""
    evidence = SecurityEvidence(
        id="ev-1",
        source="nmap",
        evidence_type="scan",
        assets=[
            _asset("192.168.1.10", hostname="server01", os="Linux",
                   services=[Service(port=22, protocol="tcp", service="ssh")]),
            _asset("192.168.1.10", hostname=None, os=None,
                   services=[Service(port=80, protocol="tcp", service="http")]),
        ],
    )
    result = normalize_evidence(evidence)
    assert len(result.assets) == 1
    assert result.assets[0].ip == "192.168.1.10"
    assert len(result.assets[0].services) == 2


def test_normalization_merges_hostname_and_os():
    """Missing hostname/os should be filled in from later scans."""
    evidence = SecurityEvidence(
        id="ev-1",
        source="nmap",
        evidence_type="scan",
        assets=[
            _asset("192.168.1.10", hostname=None, os=None),
            _asset("192.168.1.10", hostname="server01", os="Ubuntu 22.04"),
        ],
    )
    result = normalize_evidence(evidence)
    assert result.assets[0].hostname == "server01"
    assert result.assets[0].os == "Ubuntu 22.04"


def test_normalization_merges_exposure():
    """Exposure should be upgraded from 'unknown' when a later scan reports it."""
    evidence = SecurityEvidence(
        id="ev-1",
        source="nmap",
        evidence_type="scan",
        assets=[
            _asset("192.168.1.10", exposure="unknown"),
            _asset("192.168.1.10", exposure="public"),
        ],
    )
    result = normalize_evidence(evidence)
    assert result.assets[0].exposure == "public"


def test_normalization_does_not_overwrite_existing_fields():
    """A later scan should not overwrite an already-populated hostname/os."""
    evidence = SecurityEvidence(
        id="ev-1",
        source="nmap",
        evidence_type="scan",
        assets=[
            _asset("192.168.1.10", hostname="original", os="Debian 12"),
            _asset("192.168.1.10", hostname="new", os="Fedora 40"),
        ],
    )
    result = normalize_evidence(evidence)
    assert result.assets[0].hostname == "original"
    assert result.assets[0].os == "Debian 12"


def test_normalization_merges_metadata():
    """Metadata from all scans should be merged."""
    evidence = SecurityEvidence(
        id="ev-1",
        source="nmap",
        evidence_type="scan",
        assets=[
            _asset("192.168.1.10", metadata={"scan1": True}),
            _asset("192.168.1.10", metadata={"scan2": True}),
        ],
    )
    result = normalize_evidence(evidence)
    assert result.assets[0].metadata == {"scan1": True, "scan2": True}


def test_normalization_preserves_single_asset():
    """A single asset should pass through unchanged."""
    asset = _asset("192.168.1.10", hostname="server01", os="Linux",
                   services=[Service(port=22, protocol="tcp", service="ssh")])
    evidence = SecurityEvidence(
        id="ev-1", source="nmap", evidence_type="scan", assets=[asset]
    )
    result = normalize_evidence(evidence)
    assert len(result.assets) == 1
    assert result.assets[0] == asset