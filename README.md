<p align="center">
  <img src="https://img.shields.io/github/v/release/dmachard/dns-tester?logo=github&sort=semver" alt="release"/>
  <img src="https://img.shields.io/badge/pytest-44-green" alt="Py tests"/>
  <img src="https://img.shields.io/docker/pulls/dmachard/dnstester.svg" alt="docker"/>
</p>

<p align="center">
  <img src="docs/logo-dns-tester.png" alt="DNS-collector"/>
</p>

`DNS Tester` is a scalable and asynchronous tool for testing and monitoring multiple DNS servers, with support for modern DNS protocols, CLI automation, and observability.

Features:
- 🌐 REST API built with FastAPI
- 📦 Asynchronous processing using Redis and Celery
- 🧪 CLI to test DNS resolution with detailed output (IP, TTL, response time, etc.)
- 🧾 Supports loading DNS server configuration from a YAML file
- 📊 Built-in Prometheus metrics for performance and health monitoring
- 🛡️ Supports multiple DNS protocols: Do53 (UDP/TCP), DoT (TLS), DoH (HTTPS), and DoQ (QUIC)

> Example output of a full DNS test executed in parallel across 12 servers using the CLI tool:
> 
> ```
> Starting DNS lookup for domain: github.com
>   Using DNS servers: Fetching from inventory
>   API Base URL: http://localhost:5000
>   TLS Skip Verify: False
>   Task ID: 1245-3456-6789
>   Waiting for task to complete...
> 
> DNS lookup succeeded for 13 out of 13 servers (3.2896 seconds total)
> ✅  udp://1.1.1.1 - Do53 - 18.23916ms - TTL: 600s - 17.253.144.10
> ✅  udp://8.8.4.4:53 - Do53 - 15.13324ms - TTL: 515s - 17.253.144.10
> ✅  tcp://8.8.4.4:53 - Do53 - 29.19659ms - TTL: 8s - 17.253.144.10
> ✅  udp://8.8.8.8:53 - Do53 - 17.18517ms - TTL: 313s - 17.253.144.10
> ✅  tcp://8.8.8.8:53 - Do53 - 28.63772ms - TTL: 260s - 17.253.144.10
> ✅  udp://9.9.9.10 - Do53 - 28.45804ms - TTL: 600s - 17.253.144.10
> ⚠️  tcp://9.9.9.10 - Do53 - 2411.55582ms - TTL: 598s - 17.253.144.10
> ✅  udp://9.9.9.9 - Do53 - 29.70146ms - TTL: 600s - 17.253.144.10
> ✅  tcp://9.9.9.9 - Do53 - 52.66800ms - TTL: 600s - 17.253.144.10
> ✅  https://dns10.quad9.net - DoH - 236.43650ms - TTL: 599s - 17.253.144.10
> ✅  tls://dns10.quad9.net - DoT - 234.05038ms - TTL: 599s - 17.253.144.10
> ✅  https://dns9.quad9.net - DoH - 199.50676ms - TTL: 600s - 17.253.144.10
> ⚠️  tls://dns9.quad9.net - DoT - 3278.41313ms - TTL: 599s - 17.253.144.10
> ```

## 🚀 Getting Started

To get started quickly with Docker Compose:

```bash
sudo docker compose up -d
sudo docker compose exec api dnstester-cli github.com
```

For more detailed setup and usage instructions, see:
- [API Guide](docs/API_GUIDE.md) 
- [CLI Guide](docs/CLI_GUIDE.md) 
- [Configuration](docs/CONFIG.md)
- [Prometheus Monitoring](docs/MONITORING.md)

## ❤️ Contributing

Contributions are welcome!
Please read the [Developer Guide](CONTRIBUTING.md) for local setup and testing instructions.

## 🧰 Other DNS Tools

| | |
|:--:|------------|
| <a href="https://github.com/dmachard/DNS-collector" target="_blank"><img src="https://github.com/dmachard/DNS-collector/blob/main/docs/dns-collector_logo.png?raw=true" alt="DNS-collector" width="200"/></a> | Ingesting, pipelining, and enhancing your DNS logs with usage indicators, security analysis, and additional metadata. |
| <a href="https://github.com/dmachard/DNS-tester" target="_blank"><img src="https://github.com/dmachard/DNS-tester/blob/main/docs/logo-dns-tester.png?raw=true" alt="DNS-collector" width="200"/></a> | Monitoring DNS server availability and comparing response times across multiple DNS providers. |