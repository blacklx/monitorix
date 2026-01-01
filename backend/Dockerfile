# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r monitorix && useradd -r -g monitorix -u 1000 monitorix

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder to user's home
COPY --from=builder /root/.local /home/monitorix/.local

# Make sure scripts in .local are usable
ENV PATH=/home/monitorix/.local/bin:$PATH

# Copy application code
COPY . .

# Change ownership of app directory and Python packages
RUN chown -R monitorix:monitorix /app /home/monitorix/.local

# Create /tmp directory with proper permissions for admin password file
RUN mkdir -p /tmp && chmod 1777 /tmp

# Switch to non-root user
USER monitorix

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

