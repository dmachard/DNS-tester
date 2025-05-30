<p align="center">
  <img src="https://img.shields.io/github/v/release/dmachard/dns-tester?logo=github&sort=semver" alt="release"/>
  <img src="https://img.shields.io/badge/pytest-44-green" alt="Py tests"/>
  <img src="https://img.shields.io/docker/pulls/dmachard/dnstester.svg" alt="docker"/>
</p>

<p align="center">
  <img src="docs/logo-dns-tester.png" alt="DNS-collector"/>
</p>

**DNS Tester** is a scalable and asynchronous tool for testing and monitoring multiple DNS servers, with support for modern DNS protocols, CLI automation, and observability.

🎯 Use Cases:
- 🚨 **Incident Response**: DNS issues at 3 AM? Get instant visibility across all your DNS servers.
- 🔍 **DNS Cache Validation**: Verify that all your DNS caches (datacenter, cloud, edge) resolve domains consistently. Built for testing multiple internal DNS caches simultaneously.
- ⚡ **Performance Monitoring**: Compare response times across your distributed DNS infrastructure
- 📊 **Continuous Health Monitoring**: Track DNS performance with built-in Prometheus metrics
- 🛡️ **Multi-Protocol Support**: Handle mixed environments with Do53, DoT, DoH, and DoQ

> Example output of a full DNS test executed in parallel across 7 servers using the CLI tool:
> 
> ```
> Starting DNS lookup for domain: internal.company.com
> DNS lookup succeeded for 7 out of 7 servers (3.2896 seconds total)
> ✅  udp://cache-dc1.company.com - Do53 - 18.23916ms - TTL: 600s - 10.1.1.100
> ✅  udp://cache-dc2.company.com:53 - Do53 - 15.13324ms - TTL: 515s - 10.1.1.100
> ✅  tcp://cache-aws.company.com:53 - Do53 - 29.19659ms - TTL: 8s - 10.1.1.100
> ✅  udp://cache-gcp.company.com:53 - Do53 - 17.18517ms - TTL: 313s - 10.1.1.100
> ⚠️  tcp://cache-edge.company.com - Do53 - 2411.55582ms - TTL: 598s - 10.1.1.100
> ✅  https://doh.company.com - DoH - 236.43650ms - TTL: 599s - 10.1.1.100
> ⚠️  tls://dot.company.com - DoT - 3278.41313ms - TTL: 599s - 10.1.1.100
> ```

## 🚀 Getting Started

To get started quickly with Docker Compose:

```bash
sudo docker compose up -d
sudo docker compose exec api dnstester-cli internal.company.com
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
| <a href="https://github.com/dmachard/DNS-tester" target="_blank"><img src="https://github.com/dmachard/DNS-tester/blob/main/docs/logo-dns-tester.png?raw=true" alt="DNS-collector" width="200"/></a> | Validate consistency and performance across enterprise DNS cache infrastructure at scale. Built for testing multiple internal DNS caches simultaneously. |
