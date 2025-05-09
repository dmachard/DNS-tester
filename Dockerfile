# Stage 1: Build `q` binary
FROM golang:1.24 AS builder

WORKDIR /app

ARG Q_VERSION=v0.19.2

# Clone and build `q`
RUN git clone --depth 1 --branch ${Q_VERSION} https://github.com/natesales/q.git /tmp/q-src && \
    cd /tmp/q-src && \
    go mod tidy && \
    go build -o q 

# Stage 2: Python app with `q` binary
FROM python:3.13-slim

WORKDIR /app

# Copy the built `q` binary from the builder stage
COPY --from=builder /tmp/q-src/q /usr/local/bin/q
RUN chmod +x /usr/local/bin/q && q --version

RUN apt-get update && \
    apt-get install -y dnsutils && \
    # Clean up
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --shell /bin/bash dnstester
USER dnstester

COPY --chown=dnstester:dnstester . .

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "5000"]

