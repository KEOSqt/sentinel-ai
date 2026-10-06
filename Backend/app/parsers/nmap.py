import xml.etree.ElementTree as ET

from app.schemas.evidence import Asset, SecurityEvidence, Service


class NmapParser:

    def parse(self, file_path: str) -> SecurityEvidence:
        tree = ET.parse(file_path)
        root = tree.getroot()

        assets = []

        for host in root.findall("host"):

            # Get IP address
            address_element = host.find("address")

            if address_element is None:
                continue

            ip = address_element.get("addr")

            # Get hostname
            hostname = None

            hostname_element = host.find("./hostnames/hostname")

            if hostname_element is not None:
                hostname = hostname_element.get("name")

            # Get operating system
            os_name = None

            os_element = host.find("./os/osmatch")

            if os_element is not None:
                os_name = os_element.get("name")

            # Get services
            services = []

            for port_element in host.findall("./ports/port"):

                port = int(port_element.get("portid"))
                protocol = port_element.get("protocol")

                service_element = port_element.find("service")

                if service_element is None:
                    continue

                service_name = service_element.get("name")
                product = service_element.get("product")
                version = service_element.get("version")

                # Build a readable version string
                if product and version:
                    service_version = f"{product} {version}"
                elif product:
                    service_version = product
                else:
                    service_version = version

                services.append(
                    Service(
                        port=port,
                        protocol=protocol,
                        service=service_name,
                        version=service_version,
                    )
                )

            # Create the asset
            asset = Asset(
                ip=ip,
                hostname=hostname,
                os=os_name,
                services=services,
            )

            assets.append(asset)

        return SecurityEvidence(assets=assets)