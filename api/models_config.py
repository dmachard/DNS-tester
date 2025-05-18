
from typing import List, Optional, Annotated
from pydantic import BaseModel, conint, model_validator
from enum import Enum
import ipaddress

PortType = Annotated[int, conint(gt=0, le=65535)]

class ServiceType(str, Enum):
    do53_udp = "do53/udp"
    do53_tcp = "do53/tcp"
    dot = "dot"
    doh = "doh"
    doq = "doq"

class DNSServer(BaseModel):
    ip: Optional[str] = None
    port: Optional[PortType] = None
    hostname: Optional[str] = None
    services: List[ServiceType]
    tags: Optional[List[str]] = None

    @model_validator(mode="before")
    def validate_ip_or_hostname(cls, values):
        ip = values.get("ip")
        hostname = values.get("hostname")

        if not ip and not hostname:
            raise ValueError("At least one of 'ip' or 'hostname' must be provided.")

        if ip:
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                raise ValueError(f"Invalid IP address: {ip}")

        return values

    @model_validator(mode="after")
    def validate_do53_requires_ip(cls, values):
        if any(s in [ServiceType.do53_udp, ServiceType.do53_tcp] for s in values.services):
            if not values.ip:
                raise ValueError("do53/udp and do53/tcp require an IP address (not just a hostname).")
        return values
class APIConfig(BaseModel):
    servers: List[DNSServer]
