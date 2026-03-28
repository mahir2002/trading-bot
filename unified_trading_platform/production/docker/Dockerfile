# 🐳 Unified Trading Platform - Production Docker Image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_HOME=/app
ENV USER_NAME=trading
ENV USER_UID=1000

# Create non-root user for security
RUN groupadd -r ${USER_NAME} && \
    useradd -r -g ${USER_NAME} -u ${USER_UID} -d ${APP_HOME} -s /bin/bash ${USER_NAME}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    git \
    postgresql-client \
    redis-tools \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR ${APP_HOME}

# Copy requirements first for better caching
COPY requirements.txt requirements_production.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_production.txt

# Copy application code
COPY unified_trading_platform/ ./unified_trading_platform/
COPY *.py ./
COPY *.md ./
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p data logs backups temp && \
    chown -R ${USER_NAME}:${USER_NAME} ${APP_HOME}

# Switch to non-root user
USER ${USER_NAME}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"

# Expose ports
EXPOSE 8080 8050 9090

# Default command
CMD ["python", "unified_trading_platform/start_platform.py"] 