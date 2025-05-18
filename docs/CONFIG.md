
# DNS Tester – YAML Configuration Support

The DNS Tester supports loading DNS server configuration from a YAML file, offering a simpler and more flexible alternative to static Ansible inventories.

When no dns_servers are explicitly provided in a request, the API will load the DNS server list from a structured YAML configuration.

```yaml
servers:
  - ip: "8.8.8.8"
    port: 53
    services: ["do53/udp", "do53/tcp"]
    tags: ["DNS_GOOGLE"]

  - ip: "8.8.4.4"
    port: 53
    services: ["do53/udp", "do53/tcp"]

  - ip: "9.9.9.9"
    hostname: "dns9.quad9.net"
    services: ["do53/udp", "do53/tcp", "dot", "doh"]
    tags: ["DNS_QUAD9"]
```
## Field Definitions

Each server entry can include the following fields:
- ip (optional): IPv4 or IPv6 address of the DNS server
- hostname (optional): Fully qualified domain name (used for DoT, DoH, DoQ)
- port (optional): Custom port (defaults depend on protocol)
- services (required): List of supported protocols. Valid values: do53/udp, do53/tcp, dot, doh, doq
- tags (optional): List of descriptive tags for classification or filtering

> At least one of ip or hostname must be specified.
> do53/udp and do53/tcp require a valid IP address.