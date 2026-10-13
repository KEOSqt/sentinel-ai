from app.schemas.evidence import SecurityEvidence


def test_security_evidence():
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