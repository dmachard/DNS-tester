# DNS Tester – CLI Usage

DNS Tester includes a CLI tool for performing DNS lookups directly from the command line.

## Running the CLI

Before running the CLI, start the Docker services:

```bash
sudo docker compose up -d
```

After the services are running, use the CLI inside the `api` container:

```bash
sudo docker compose exec api dnstester-cli <query> [dns_servers...] [options]
```

---

## Syntax

```bash
dnstester-cli <query> [dns_servers...] \
  [--qtype <A|AAAA|MX|CNAME>] \
  [--reverse | -r] \
  [--api-url <api_url>] \
  [--insecure] \
  [--debug | -d] \
  [--pretty | -p] \
  [--warn-threshold <seconds>] \
  [--input-file <file>] \
  [--version | -v]
```

## Arguments

* `<query>`: Domain name or IP address to query.
* `[dns_servers...]`: List of DNS servers (e.g., `udp://8.8.8.8`, `tls://1.1.1.1`). If not provided, servers are fetched from inventory.
* `--qtype`: DNS query type for forward lookups (`A`, `AAAA`, `MX`, `CNAME`). Default: `A`.
* `--reverse`, `-r`: Perform a reverse DNS lookup (PTR).
* `--api-url`: Base URL of the API. Default: `http://localhost:5000`.
* `--insecure`: Skip TLS certificate verification.
* `--debug`, `-d`: Show detailed debug output and error messages.
* `--pretty`, `-p`: Enable emoji-enhanced output.
* `--warn-threshold`: Response time threshold in seconds for warning messages. Default: `1.0`.
* `--input-file`: Read multiple domains from a file (must exist inside the container).
* `--version`, `-v`: Show package version and exit.

---

## Input File Format

The file must contain lines in the following format: `TYPE;domain`

Example `domains.txt`:
```text
A;example.com
AAAA;example.org
MX;gmail.com
```
Supported types:

* `A`
* `AAAA`
* `MX`
* `CNAME`

>Empty lines are ignored. Invalid lines are skipped.
### Important: File Paths in Docker
When using the `--input-file` option, the path must point to a file **inside the container's file system**, not your host machine. To use a local file, you must mount it as a volume.

---

## Example usage

### Start the services

```bash
sudo docker compose up -d
```

### Query a domain using specific DNS servers

```bash
sudo docker compose exec api dnstester-cli github.com udp://8.8.8.8 udp://1.1.1.1 --qtype A
```

### Query a domain without specifying DNS servers

```bash
sudo docker compose exec api dnstester-cli github.com --qtype AAAA
```

### Query a domain with a custom API URL

```bash
sudo docker compose exec api dnstester-cli github.com udp://8.8.8.8 --api-url http://custom-api-url:5000
```

### Query a domain with insecure TLS verification

```bash
sudo docker compose exec api dnstester-cli github.com tls://1.1.1.1 --insecure
```

### Perform a reverse lookup for an IP

```bash
sudo docker compose exec api dnstester-cli 8.8.8.8 --reverse
```

### Query many domains from a file

```bash
sudo docker compose exec api dnstester-cli --input-file domains.txt
```

### Show version

```bash
sudo docker compose exec api dnstester-cli --version
```

---

## Behavior
* **Auto-detection**: If the query is an IP address, the CLI automatically performs a reverse lookup.
* **Force Reverse**: If `--reverse` is used, the CLI performs a PTR lookup regardless of other flags.
* **Batch Processing**: When using `--input-file`, the CLI processes each line and outputs results sequentially.