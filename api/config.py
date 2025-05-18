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
    for server in config.servers:
        for service in server.services:
            service = service.strip()
            if '/' in service:
                service_type, proto = service.split('/', 1)
            else:
                service_type, proto = service, None

            if service_type == 'do53':
                scheme = proto if proto else 'udp'
                target = f"{scheme}://{server.ip}"
                if server.port:
                    target += f":{server.port}"
                dns_info_list.append({"target": target, "tags": server.tags})

            elif service_type == 'doh':
                host = server.hostname if server.hostname else server.ip
                target = f"https://{host}"
                if server.port:
                    target += f":{server.port}"
                dns_info_list.append({"target": target, "tags": server.tags})

            elif service_type == 'dot':
                host = server.hostname if server.hostname else server.ip
                target = f"tls://{host}"
                if server.port:
                    target += f":{server.port}"
                dns_info_list.append({"target": target, "tags": server.tags})

            elif service_type == 'doq':
                host = server.hostname if server.hostname else server.ip
                target = f"quic://{host}"
                if server.port:
                    target += f":{server.port}"
                dns_info_list.append({"target": target, "tags": server.tags})
    return dns_info_list