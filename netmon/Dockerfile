FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nmap \
    speedtest-cli \
    sqlite3 \
    postgresql-client \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up app directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY . .

# Create scripts directory and ensure proper permissions
RUN mkdir -p /app/scripts \
    && chmod +x /app/entrypoint.sh \
    && chmod +x /app/scripts/network_monitor.sh

# Set the entrypoint using exec form with bash
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]