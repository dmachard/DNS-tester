from enum import Enum
from dataclasses import dataclass


class DomainType(Enum):
    A = "A"
    AAAA = "AAAA"
    MX = "MX"
    CNAME = "CNAME"


@dataclass
class Domain:
    domain: str
    domain_type: DomainType


def parse_line(line: str) -> Domain | None:
    line = line.strip()
    if not line:
        return None

    parts = line.split(";", 1)
    if len(parts) != 2:
        return None

    record_type_str, domain_name = parts[0].strip().upper(), parts[1].strip()

    try:
        record_type = DomainType(record_type_str)
    except ValueError:
        return None

    return Domain(domain=domain_name, domain_type=record_type)


def input_file(file_path: str) -> list[Domain]:
    domains: list[Domain] = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            domain = parse_line(line)
            if domain is not None:
                domains.append(domain)

    return domains