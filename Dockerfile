# Stage 1: Build `q` binary
FROM golang:1.25 AS builder

WORKDIR /app

ARG Q_VERSION=v0.19.2

# Clone and build `q`
RUN git clone --depth 1 --branch ${Q_VERSION} https://github.com/natesales/q.git /tmp/q-src && \
    cd /tmp/q-src && \
    go mod tidy && \
    go build -o q 

# Stage 2: Python app with `q` binary
FROM python:3.14-slim

WORKDIR /app

# Copy the built `q` binary from the builder stage
COPY --from=builder /tmp/q-src/q /usr/local/bin/q
RUN chmod +x /usr/local/bin/q && q --version

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc pkg-config libssl-dev rustc cargo && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove build-essential gcc pkg-config libssl-dev rustc cargo && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY ./scripts/dnstester-cli.sh /usr/local/bin/dnstester-cli
RUN pip install --no-cache-dir -r requirements.txt && \
    useradd --create-home --shell /bin/bash dnstester && \
    chmod +x /usr/local/bin/dnstester-cli && \
    chown dnstester:dnstester /usr/local/bin/dnstester-cli

USER dnstester
COPY --chown=dnstester:dnstester . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5000"]

