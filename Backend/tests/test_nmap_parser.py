from pathlib import Path

import pytest

from app.parsers.nmap import NmapParseError, NmapParser

FIXTURE = Path(__file__).parent / "fixtures" / "sample_nmap.xml"


def test_parse_file_extracts_assets_and_services():
    evidence = NmapParser().parse_file(FIXTURE)

    assert evidence.source == "nmap"
    assert len(evidence.assets) == 2

    server = evidence.assets[0]
    assert server.ip == "192.168.1.10"
    assert server.hostname == "server01.local"
    assert server.os == "Linux 4.15 - 5.8"
    assert len(server.services) == 3

    ssh = server.services[0]
    assert ssh.port == 22
    assert ssh.service == "ssh"
    assert ssh.state == "open"
    assert "OpenSSH" in ssh.version


def test_parse_rejects_non_nmap_xml():
    with pytest.raises(NmapParseError):
        NmapParser().parse_bytes(b"<foo/>")


def test_parse_rejects_xxe():
    payload = b'''<?xml version="1.0"?>
    <!DOCTYPE nmaprun [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
    <nmaprun>&xxe;</nmaprun>'''
    with pytest.raises(NmapParseError):
        NmapParser().parse_bytes(payload)


def test_parse_rejects_invalid_xml():
    with pytest.raises(NmapParseError):
        NmapParser().parse_bytes(b"not xml")
