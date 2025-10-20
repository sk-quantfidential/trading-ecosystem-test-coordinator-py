FROM python:3.13-slim

WORKDIR /app

# Install system dependencies including Docker CLI
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
#    curl \
#    && curl -fsSL https://get.docker.com -o get-docker.sh \
#    && sh get-docker.sh \
#    && rm get-docker.sh \

# Copy test-coordinator-data-adapter-py dependency first
COPY test-coordinator-data-adapter-py/ /app/test-coordinator-data-adapter-py/

# Copy requirements and install test-coordinator
COPY test-coordinator-py/pyproject.toml ./

# Install test-coordinator-data-adapter first
RUN pip install --no-cache-dir /app/test-coordinator-data-adapter-py

# Install trading-system-engine (without trading-data-adapter since already installed)
RUN pip install --no-cache-dir -e .

# Copy source code (directly to /app so trading_system is importable)
COPY test-coordinator-py/src/ ./

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/v1/health')"
#    CMD curl -f http://localhost:8080/api/v1/health || exit 1

EXPOSE 8080 50051

CMD ["python", "-m", "test_coordinator.main"]