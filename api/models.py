from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Literal, Optional

# List of allowed protocols
ALLOWED_PROTOCOLS = ["udp://", "tcp://", "https://", "quic://", "tls://"]

class DNSLookup(BaseModel):
    domain: str = Field(..., description="Domain name to query")
    dns_servers: List[str] = Field(..., description="List of DNS servers to use")
    qtype: Literal["A", "CNAME", "PTR", "TXT", "AAAA"] = Field(..., description="DNS query type")
    tls_insecure_skip_verify: bool = Field(False, title="TLS Insecure Skip Verify", description="Skip TLS certificate verification (for TLS-based queries)")


    @field_validator("dns_servers")
    @classmethod
    def check_dns_protocol(cls, v):
        # Validate that each DNS server starts with a valid protocol
        for server in v:
            if not any(server.startswith(protocol) for protocol in ALLOWED_PROTOCOLS):
                raise ValueError(f"DNS server '{server}' must start with one of {', '.join(ALLOWED_PROTOCOLS)}")
        return v

class DNSAnswer(BaseModel):
    """Represents a single DNS answer record."""
    name: str = Field(..., description="The domain name in the answer.")
    type: str = Field(..., description="The DNS record type (e.g., A, AAAA, CNAME, etc.).")
    ttl: int = Field(..., description="Time-to-live value of the record.")
    value: str = Field(..., description="The resolved value of the record.")
    
class DNSLookupResult(BaseModel):
    """Represents the result of a DNS lookup request."""
    command_status: str = Field(..., description="Status of the DNS command execution (ok/error).")
    time_ms: Optional[float] = Field(None, description="Time taken for the DNS query in milliseconds.")
    rcode: Optional[str] = Field(None, description="Response code (e.g., NoError, NXDomain, etc.).")
    name: Optional[str] = Field(None, description="The queried domain name.")
    qtype: Optional[str] = Field(None, description="Query type (A, AAAA, CNAME, etc.).")
    answers: Optional[List[DNSAnswer]] = Field(None, description="List of DNS answer records.")
    error: Optional[str] = Field(None, description="Error message if the query failed.")

class DNSLookupStatus(BaseModel):
    """Represents the response of a DNS task lookup request."""
    task_id: str = Field(..., description="Unique identifier for the DNS lookup task.")
    task_status: str = Field(..., description="Current status of the task (e.g., PENDING, SUCCESS).")
    result: Dict[str, DNSLookupResult] = Field(
        ..., description="Results of the DNS query for each server."
    )

