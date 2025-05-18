import pytest
import yaml
from pydantic import ValidationError

from api.models_config import APIConfig, DNSServer
from api.config import get_dns_servers_from_yaml

example_yaml = """
servers:
  - ip: "8.8.8.8"
    port: 53
    services: ["do53/udp", "do53/tcp" ]
    tags: [ "DNS_GOOGLE" ]

  - ip: "8.8.4.4"
    port: 53
    services: ["do53/udp", "do53/tcp" ]

  - ip: "9.9.9.9"
    hostname: "dns9.quad9.net"
    services: [ "do53/udp", "do53/tcp", "dot", "doh" ]
    tags: [ "DNS_QUAD9" ]

  - ip: "1.1.1.1"
    services: [ "do53/udp" ]
    tags: [ "DNS_CLOUDFLARE" ]
"""

def test_config_valid():
    data = yaml.safe_load(example_yaml)
    config = APIConfig(**data)
    assert len(config.servers) == 4
    assert config.servers[0].ip == "8.8.8.8"
    assert "do53/udp" in config.servers[0].services

def test_config_invalid_ip_format():
    bad_data = {
        "servers": [
            {
                "ip": "999.999.999.999",
                "services": ["dot"]
            }
        ]
    }
    with pytest.raises(ValidationError, match="Invalid IP address"):
        APIConfig(**bad_data)

def test_config_missing_ip_and_hostname():
    bad_data = {
        "servers": [
            {
                "services": ["dot"]
            }
        ]
    }
    with pytest.raises(ValidationError, match="At least one of 'ip' or 'hostname' must be provided"):
        APIConfig(**bad_data)

def test_config_do53_requires_ip():
    bad_data = {
        "servers": [
            {
                "hostname": "dns.example.com",
                "services": ["do53/udp"]
            }
        ]
    }
    with pytest.raises(ValidationError, match="do53/udp and do53/tcp require an IP address"):
        APIConfig(**bad_data)

def test_config_only_hostname_with_dot_service():
    server = DNSServer(
        hostname="dns.example.com",
        services=["dot"]
    )
    assert server.hostname == "dns.example.com"
    assert "dot" in server.services

def test_get_dns_servers_from_yaml():
    config_data = yaml.safe_load(example_yaml)
    config = APIConfig(**config_data)
    dns_info = get_dns_servers_from_yaml(config)

    expected = [
        {'target': 'udp://8.8.8.8:53', 'tags': ['DNS_GOOGLE']},
        {'target': 'tcp://8.8.8.8:53', 'tags': ['DNS_GOOGLE']},
        {'target': 'udp://8.8.4.4:53', 'tags': []},
        {'target': 'tcp://8.8.4.4:53', 'tags': []},
        {'target': 'udp://9.9.9.9', 'tags': ['DNS_QUAD9']},
        {'target': 'tcp://9.9.9.9', 'tags': ['DNS_QUAD9']},
        {'target': 'tls://dns9.quad9.net', 'tags': ['DNS_QUAD9']},
        {'target': 'https://dns9.quad9.net', 'tags': ['DNS_QUAD9']},
        {'target': 'udp://1.1.1.1', 'tags': ['DNS_CLOUDFLARE']},
    ]

    assert dns_info == expected