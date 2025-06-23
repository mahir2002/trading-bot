# AI Crypto Trading Bot - Docker Container
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p logs data

# Copy application files
COPY *.py ./
COPY config.env.example ./
COPY README.md ./

# Create a non-root user for security (Enhanced)
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g 1001 -m -s /bin/sh appuser && \
    mkdir -p /app/logs /app/data /app/config && \
    chown -R 1001:1001 /app && \
    chmod -R 755 /app && \
    chmod 644 /app/data && \
    chmod 600 /app/config

# Copy application files with proper ownership
COPY --chown=1001:1001 . /app/

# Additional security hardening
RUN find /app -type f -name '*.py' -exec chmod 644 {} \; 2>/dev/null || true && \
    find /app -type d -exec chmod 755 {} \; 2>/dev/null || true

# Enhanced security labels
LABEL security.non_root="true" \
      security.user="appuser" \
      security.uid="1001" \
      security.gid="1001" \
      security.compliance="cis-docker-benchmark" \
      security.level="high"

# Switch to non-root user
USER 1001:1001

# Expose ports
EXPOSE 8050 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8050/health || exit 1

# Default command (can be overridden)
CMD ["python", "run_bot.py", "--dashboard"] 