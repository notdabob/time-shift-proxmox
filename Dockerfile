# Time-Shift Proxy Container
# Provides SSL certificate time manipulation for accessing systems with expired certificates

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ntpdate \
    openssl \
    ca-certificates \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY bin/ /app/bin/
COPY lib/ /app/lib/
COPY etc/ /app/etc/

# Create necessary directories
RUN mkdir -p /app/config \
    /app/logs \
    /app/certs \
    && chmod +x /app/bin/*.py

# Copy startup script
COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose port
EXPOSE 8090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8090/health || exit 1

# Start the application
CMD ["/app/start.sh"]