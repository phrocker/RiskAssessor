# Multi-stage build for RiskAssessor
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Install the package
RUN pip install --no-cache-dir -e .

# Create directory for catalog data
RUN mkdir -p /app/.risk_assessor

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd -m -u 1000 riskassessor && \
    chown -R riskassessor:riskassessor /app
USER riskassessor

# Default command
CMD ["risk-assessor", "--help"]
