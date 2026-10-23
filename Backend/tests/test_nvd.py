import json
from unittest.mock import patch, MagicMock

from app.services.vulns import nvd


def test_lookup_disabled():
    """When NVD is disabled, lookup should return empty list."""
    from app.core.config import settings
    original = settings.nvd_enabled
    settings.nvd_enabled = False
    try:
        result = nvd.lookup("openssh", "7.4")
        assert result == []
    finally:
        settings.nvd_enabled = original


def test_lookup_no_product():
    """Lookup with no product should return empty list."""
    from app.core.config import settings
    original = settings.nvd_enabled
    settings.nvd_enabled = True
    try:
        result = nvd.lookup(None, "7.4")
        assert result == []
    finally:
        settings.nvd_enabled = original


def test_lookup_success():
    """Lookup should return parsed vulnerabilities from NVD API."""
    from app.core.config import settings
    original_enabled = settings.nvd_enabled
    original_api_key = settings.nvd_api_key
    settings.nvd_enabled = True
    settings.nvd_api_key = None
    try:
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = json.dumps({
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2023-38408",
                        "descriptions": [{"lang": "en", "value": "OpenSSH ssh-agent RCE"}],
                        "metrics": {
                            "cvssMetricV31": [
                                {"cvssData": {"baseScore": 9.8}}
                            ]
                        }
                    }
                }
            ]
        }).encode()

        with patch("urllib.request.urlopen", return_value=mock_response):
            results = nvd.lookup("openssh", "7.4")
            assert len(results) == 1
            assert results[0].id == "CVE-2023-38408"
            assert results[0].severity.value == "CRITICAL"
    finally:
        settings.nvd_enabled = original_enabled
        settings.nvd_api_key = original_api_key