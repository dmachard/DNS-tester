# Stage 1: Build `q` binary
FROM golang:1.26-alpine AS builder

WORKDIR /app

ARG Q_VERSION=v0.19.2

# Clone and build `q`
RUN apk add --no-cache git && \
    git clone --depth 1 --branch ${Q_VERSION} https://github.com/natesales/q.git /tmp/q-src && \
    cd /tmp/q-src && \
    go mod tidy && \
    CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o q

# Stage 2: Python app with `q` binary
FROM python:3.14-slim

WORKDIR /app

# Copy the built `q` binary from the builder stage
COPY --from=builder /tmp/q-src/q /usr/local/bin/q
RUN chmod +x /usr/local/bin/q && q --version

# Copy requirements first so Docker can cache this layer
COPY requirements.txt .

# Install dependencies and build tools temporarily
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc pkg-config libssl-dev rustc cargo && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove build-essential gcc pkg-config libssl-dev rustc cargo && \
    rm -rf /var/lib/apt/lists/*

COPY ./scripts/dnstester-cli.sh /usr/local/bin/dnstester-cli
RUN useradd --create-home --shell /bin/bash dnstester && \
    chmod +x /usr/local/bin/dnstester-cli && \
    chown dnstester:dnstester /usr/local/bin/dnstester-cli

USER dnstester
COPY --chown=dnstester:dnstester . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5000"]

