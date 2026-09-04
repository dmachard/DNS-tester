# Stage 1: Build `q` binary
FROM golang:1.27-alpine AS q-builder

WORKDIR /app

ARG Q_VERSION=v0.19.2

# Clone and build `q`
RUN apk add --no-cache git && \
    git clone --depth 1 --branch ${Q_VERSION} https://github.com/natesales/q.git /tmp/q-src && \
    cd /tmp/q-src && \
    go mod tidy && \
    CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o q

# Stage 2: Build Python dependencies on Alpine
FROM python:3.14-alpine AS py-builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y pip && \
    find /opt/venv -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -name '*.pyc' -delete

# Stage 3: Minimal Alpine runtime
FROM python:3.14-alpine AS runtime

WORKDIR /app

# Copy the built `q` binary
COPY --from=q-builder /tmp/q-src/q /usr/local/bin/q
RUN chmod +x /usr/local/bin/q && q --version

# Copy Python virtual environment
COPY --from=py-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN adduser -D dnstester
USER dnstester

COPY --chown=dnstester:dnstester . .

ENTRYPOINT ["python", "entrypoint.py"]
CMD ["api"]
