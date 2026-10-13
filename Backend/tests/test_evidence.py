from app.models import Asset, SecurityEvidence, Service


def test_security_evidence_parses_from_dict():
    evidence = SecurityEvidence(
        assets=[
            {
                "ip": "192.168.1.10",
                "hostname": "server01",
                "os": "Linux",
                "services": [
                    {
                        "port": 22,
                        "protocol": "tcp",
                        "service": "ssh",
                        "version": "OpenSSH 8.2",
                    }
                ],
            }
        ]
    )

    assert evidence.assets[0].ip == "192.168.1.10"
    assert evidence.assets[0].services[0].port == 22


def test_service_defaults_apply_when_absent():
    service = Service(port=443)

    assert service.protocol == "tcp"
    assert service.service == "unknown"
    assert service.state == "open"
    assert service.version is None


def test_asset_defaults():
    asset = Asset(ip="10.0.0.1")

    assert asset.hostname is None
    assert asset.exposure == "unknown"
    assert asset.services == []
    assert asset.metadata == {}
    # Ids are generated per instance so findings/assets never collide.
    assert asset.id
    assert Asset(ip="10.0.0.1").id != asset.id