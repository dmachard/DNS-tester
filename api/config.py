import yaml
import os
from api.models_config import APIConfig

def load_yaml_config(file_path: str) -> APIConfig:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Config file not found: {file_path}")

    with open(file_path, "r") as f:
        raw_data = yaml.safe_load(f)

    # Validation with Pydantic
    return APIConfig(**raw_data)

def get_dns_servers_from_yaml(config: APIConfig) -> list:
    """
    Extract DNS servers from the loaded YAML configuration.
    """
    dns_info_list = []
    
    # Mapping of service types to their URL schemes
    service_schemes = {
        'doh': 'https',
        'dot': 'tls',
        'doq': 'quic'
    }
    
    def add_dns_entry(host: str, scheme: str, port: int, tags: list):
        """Add a DNS entry to the list"""
        target = f"{scheme}://{host}"
        if port:
            target += f":{port}"
        dns_info_list.append({"target": target, "tags": tags})
    
    for server in config.servers:
        for service in server.services:
            service = service.strip()
            if '/' in service:
                service_type, proto = service.split('/', 1)
            else:
                service_type, proto = service, None
            
            tags = server.tags if server.tags is not None else []
            
            if service_type == 'do53':
                scheme = proto if proto else 'udp'
                add_dns_entry(server.ip, scheme, server.port, tags)
            
            elif service_type in service_schemes:
                scheme = service_schemes[service_type]
                
                # Add entry for hostname if present
                if server.hostname:
                    add_dns_entry(server.hostname, scheme, server.port, tags)
                
                # Add entry for IP if present
                if server.ip:
                    add_dns_entry(server.ip, scheme, server.port, tags)
    
    return dns_info_list