from datetime import UTC, datetime
from pathlib import Path

from defusedxml import ElementTree as DET
from defusedxml.common import DefusedXmlException

from app.models import Asset, SecurityEvidence, Service


class NmapParseError(Exception):
    pass


class NmapParser:
    def parse_file(self, file_path: str | Path) -> SecurityEvidence:
        try:
            return self.parse_bytes(Path(file_path).read_bytes())
        except OSError as exc:
            raise NmapParseError(f"cannot read file: {exc}") from exc

    def parse_bytes(self, payload: bytes) -> SecurityEvidence:
        try:
            root = DET.fromstring(payload)
        except DefusedXmlException as exc:
            raise NmapParseError(f"unsafe XML rejected: {exc}") from exc
        except Exception as exc:
            raise NmapParseError(f"invalid XML: {exc}") from exc

        if root.tag != "nmaprun":
            raise NmapParseError("not an Nmap XML document (missing <nmaprun>)")

        assets: list[Asset] = []
        scan_start = root.get("startstr") or None
        start_ts: datetime | None = None
        if root.get("start"):
            try:
                start_ts = datetime.fromtimestamp(int(root.get("start")), tz=UTC)
            except (ValueError, OSError):
                start_ts = None

        for host in root.findall("host"):
            status = host.find("status")
            if status is not None and status.get("state") not in (None, "up"):
                continue

            addresses = [a.get("addr") for a in host.findall("address") if a.get("addr")]
            ip = next((a for a in addresses if _looks_like_ip(a)), addresses[0] if addresses else None)
            if not ip:
                continue

            hostname = None
            hn = host.find("./hostnames/hostname")
            if hn is not None:
                hostname = hn.get("name")

            os_name = None
            os_match = host.find("./os/osmatch")
            if os_match is not None:
                os_name = os_match.get("name")

            services: list[Service] = []
            for port_element in host.findall("./ports/port"):
                state_element = port_element.find("state")
                state = state_element.get("state") if state_element is not None else "unknown"

                service_element = port_element.find("service")
                if service_element is None:
                    continue

                try:
                    port = int(port_element.get("portid", "0"))
                except ValueError:
                    continue

                services.append(
                    Service(
                        port=port,
                        protocol=port_element.get("protocol", "tcp"),
                        service=service_element.get("name", "unknown"),
                        product=service_element.get("product"),
                        version=_build_version(service_element),
                        state=state,
                    )
                )

            assets.append(
                Asset(
                    ip=ip,
                    hostname=hostname,
                    os=os_name,
                    services=services,
                    metadata={"addresses": addresses, "state": (status.get("state") if status is not None else "unknown")},
                )
            )

        return SecurityEvidence(
            source="nmap",
            evidence_type="network_scan",
            timestamp=start_ts or datetime.now(UTC),
            assets=assets,
            metadata={"scanner": "nmap", "scan_start": scan_start, "asset_count": len(assets)},
        )


def _build_version(service_element) -> str | None:
    product = service_element.get("product")
    version = service_element.get("version")
    extrainfo = service_element.get("extrainfo")
    parts = [p for p in (product, version, extrainfo) if p]
    return " ".join(parts) if parts else None


def _looks_like_ip(value: str) -> bool:
    return value.replace(".", "").replace(":", "").isalnum() and any(c.isdigit() for c in value)
