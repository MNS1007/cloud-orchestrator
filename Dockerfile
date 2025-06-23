# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and gcloud CLI
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    && rm -rf /var/lib/apt/lists/*

# Install Google Cloud CLI
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - \
    && echo "deb https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update \
    && apt-get install -y google-cloud-cli \
    && rm -rf /var/lib/apt/lists/*

# Copy minimal requirements and install Python dependencies
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Copy the application code
COPY cloud_orchestrator/ ./cloud_orchestrator/
COPY creds/ ./creds/

# Set environment variables
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/creds/worker.json
ENV PORT=8080

# Expose port
EXPOSE 8080

# Create a startup script
RUN echo '#!/bin/bash\nadk web cloud_orchestrator/agents --host 0.0.0.0 --port $PORT' > /app/start.sh
RUN chmod +x /app/start.sh

# Start the application
CMD ["/app/start.sh"] 