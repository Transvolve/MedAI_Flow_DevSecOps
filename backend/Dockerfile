# backend/Dockerfile
# Multi-stage build for security and size optimization
FROM python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements-ci.txt requirements-security.txt ./
RUN pip install --no-cache-dir --user -r requirements-ci.txt -r requirements-security.txt

# ============================================================
# Final stage - minimal runtime image
# ============================================================
FROM python:3.11-slim

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r medai && useradd -r -g medai -u 1000 medai

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /root/.local /home/medai/.local

# Copy application code
COPY --chown=medai:medai app /app

# Set PATH for user-installed packages
ENV PATH=/home/medai/.local/bin:$PATH

# Switch to non-root user
USER medai

# Expose FastAPI port (8000 to match application)
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI with production settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
