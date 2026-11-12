# Multi-stage production container for FFIRE Backend API Gateway (Chapter 60)
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged system user for security compliance
RUN groupadd -g 1001 ffiregroup && \
    useradd -u 1001 -g ffiregroup -s /bin/bash -m ffireuser

# Copy installed wheels from builder stage
COPY --from=builder /root/.local /home/ffireuser/.local
ENV PATH=/home/ffireuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# One copy of the source, in /app/backend. Modules are imported by their plain names (main, models,
# worker); /app is also on the path so the sub-packages that say "backend.cases" still resolve.
# Copying the tree twice made the API load "backend.main" while the worker loaded "main": two
# copies of the same application in memory.
COPY --chown=ffireuser:ffiregroup . /app/backend
RUN touch /app/backend/__init__.py && mkdir -p /app/backend/data && chown -R ffireuser:ffiregroup /app/backend/data
WORKDIR /app/backend
ENV PYTHONPATH=/app/backend:/app

USER ffireuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
