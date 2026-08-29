# Stage 1: Build `q` binary
FROM golang:1.26-alpine AS q-builder

WORKDIR /app

ARG Q_VERSION=v0.19.12

# Clone and build `q`
RUN apk add --no-cache git && \
    git clone --depth 1 --branch ${Q_VERSION} https://github.com/natesales/q.git /tmp/q-src && \
    cd /tmp/q-src && \
    go mod tidy && \
    CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o q

# Stage 2: Build Python dependencies matching distroless python 3.13
FROM python:3.14-slim AS py-builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y pip && \
    find /opt/venv -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -name '*.pyc' -delete

# Stage 3: Minimal Distroless runtime
FROM gcr.io/distroless/python3-debian13:latest AS runtime

WORKDIR /app

# Copy the built `q` binary
COPY --from=q-builder /tmp/q-src/q /usr/local/bin/q

# Copy Python virtual environment
COPY --from=py-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:/usr/local/bin:$PATH"
ENV PYTHONPATH="/opt/venv/lib/python3.13/site-packages"

# Copy application files
COPY --chown=nonroot:nonroot . .

USER nonroot

ENTRYPOINT ["python3", "entrypoint.py"]
CMD ["api"]
