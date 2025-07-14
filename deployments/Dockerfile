# Multi-stage Dockerfile for Certify Studio

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml requirements.txt ./
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 certify && \
    mkdir -p /app /data /logs && \
    chown -R certify:certify /app /data /logs

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=certify:certify /app/.venv /app/.venv

# Copy application code
COPY --chown=certify:certify . .

# Set Python path
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# Create necessary directories
RUN mkdir -p /app/uploads /app/exports /app/temp /app/exports/videos && \
    chown -R certify:certify /app

# Switch to non-root user
USER certify

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["uvicorn", "certify_studio.main:app", "--host", "0.0.0.0", "--port", "8000"]
