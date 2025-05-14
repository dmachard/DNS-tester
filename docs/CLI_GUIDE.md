
# CLI Usage

The DNS Tester includes a CLI tool for performing DNS lookups directly from the command line.

## Running the CLI

To use the CLI from docker image, run the following command:

```bash
sudo docker compose exec api dnstester-cli <domain> [dns_servers...] [--qtype <query_type>] [--api-url <api_url>] [--insecure]
```

## Arguments

- `<domain>`: The domain name to query.
- `[dns_servers...]`: A list of DNS servers to query (e.g., `udp://8.8.8.8`). If not provided, the servers will be fetched from the inventory.
- `--qtype`: The DNS query type. Supported values are `A` (default) and `AAAA`.
- `--api-url`: The base URL of the API (default: `http://localhost:5000`).
- `--insecure`: Skip TLS certificate verification for secure DNS queries.

## Example Usage

### Query a domain or IP using specific DNS servers:
```bash
sudo docker compose exec api dnstester-cli github.com udp://8.8.8.8 udp://1.1.1.1 --qtype A
```

### Query a domain without specifying DNS servers (fetch from inventory):
```bash
sudo docker compose exec api dnstester-cli github.com --qtype AAAA
```

### Query a domain with a custom API URL:
```bash
sudo docker compose exec api dnstester-cli github.com udp://8.8.8.8 --api-url http://custom-api-url:5000
```

### Query a domain with insecure TLS verification:
```bash
sudo docker compose exec api dnstester-cli github.com udp://8.8.8.8 --insecure
```
