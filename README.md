<p align="center">
  <img src="https://img.shields.io/github/v/release/dmachard/dns-tester?logo=github&sort=semver" alt="release"/>
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
- 🧾 Integration with static Ansible inventory for DNS server config
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
> DNS lookup of 12 servers completed in 0.2900s:
>     udp://1.1.1.1 - Do53 - 14.91580ms - TTL: 59s - 140.82.121.4
>     tcp://1.1.1.1 - Do53 - 22.73039ms - TTL: 18s - 140.82.121.4
>     udp://8.8.8.8 - Do53 - 36.54281ms - TTL: 60s - 140.82.121.3
>     tcp://8.8.8.8 - Do53 - 36.22145ms - TTL: 60s - 140.82.121.3
>     udp://9.9.9.10 - Do53 - 25.82462ms - TTL: 27s - 140.82.121.4
>     tcp://9.9.9.10 - Do53 - 46.67132ms - TTL: 10s - 140.82.121.4
>     udp://9.9.9.9 - Do53 - 25.31037ms - TTL: 46s - 140.82.121.4
>     tcp://9.9.9.9 - Do53 - 41.68741ms - TTL: 27s - 140.82.121.4
>     https://dns10.quad9.net - DoH - 238.26471ms - TTL: 60s - 140.82.121.4
>     tls://dns10.quad9.net - DoT - 232.89234ms - TTL: 1s - 140.82.121.3
>     https://dns9.quad9.net - DoH - 234.11824ms - TTL: 5s - 140.82.121.4
>     tls://dns9.quad9.net - DoT - 278.54105ms - TTL: 58s - 140.82.121.4
```

## 🚀 Getting Started

To get started quickly with Docker Compose:

```bash
sudo docker compose up -d
sudo docker compose exec api dnstester-cli github.com udp://8.8.8.8 udp://1.1.1.1 --qtype A
```

For more detailed setup and usage instructions, see:
- [API Guide](docs/API_GUIDE.md) 
- [CLI Guide](docs/CLI_GUIDE.md) 
- [Ansible Inventory & Prometheus Monitoring](docs/INTEGRATIONS.md)

## ❤️ Contributing

Contributions are welcome!
Please read the [Developer Guide](CONTRIBUTING.md) for local setup and testing instructions.

## 🧰 Other DNS Tools

| | |
|:--:|------------|
| <a href="https://github.com/dmachard/DNS-collector" target="_blank"><img src="https://github.com/dmachard/DNS-collector/blob/main/docs/dns-collector_logo.png?raw=true" alt="DNS-collector" width="200"/></a> | Ingesting, pipelining, and enhancing your DNS logs with usage indicators, security analysis, and additional metadata. |
| <a href="https://github.com/dmachard/DNS-tester" target="_blank"><img src="https://github.com/dmachard/DNS-tester/blob/main/docs/logo-dns-tester.png?raw=true" alt="DNS-collector" width="200"/></a> | Monitoring DNS server availability and comparing response times across multiple DNS providers. |