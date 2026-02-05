# LUMINA Dockerfile
# License Unified Management & Identity Network Authorization
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        default-libmysqlclient-dev \
        pkg-config \
        su-exec \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install uv (fast Python package manager) and dependencies
RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache -r requirements.txt

# Copy application code
COPY . .

# Copy entrypoint script
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create non-root user
RUN groupadd -r lumina && \
    useradd -r -g lumina -u 1000 lumina

# Create necessary directories
RUN mkdir -p data logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/ping')"

# Run as root to fix permissions, then drop to lumina user
ENTRYPOINT ["/entrypoint.sh"]
