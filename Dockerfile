# Stage 1: Build `q` binary
FROM golang:1.26-alpine AS q-builder

WORKDIR /app

ARG Q_VERSION=v0.19.2

# Clone and build `q`
RUN apk add --no-cache git && \
    git clone --depth 1 --branch ${Q_VERSION} https://github.com/natesales/q.git /tmp/q-src && \
    cd /tmp/q-src && \
    go mod tidy && \
    CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o q

# Stage 2: Build Python dependencies in a virtual environment
FROM python:3.14-slim AS py-builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc pkg-config libssl-dev rustc cargo && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Minimal runtime image
FROM python:3.14-slim AS runtime

WORKDIR /app

# Copy the built `q` binary
COPY --from=q-builder /tmp/q-src/q /usr/local/bin/q
RUN chmod +x /usr/local/bin/q && q --version

# Copy the virtual environment with all installed packages
COPY --from=py-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./scripts/dnstester-cli.sh /usr/local/bin/dnstester-cli
RUN useradd --create-home --shell /bin/bash dnstester && \
    chmod +x /usr/local/bin/dnstester-cli && \
    chown dnstester:dnstester /usr/local/bin/dnstester-cli

USER dnstester
COPY --chown=dnstester:dnstester . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5000"]

