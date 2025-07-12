# Multi-stage build for production
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Set work directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create virtual environment
RUN poetry config virtualenvs.create false

# Install Python dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.local/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    graphviz \
    libcairo2 \
    libpango-1.0-0 \
    libglib2.0-0 \
    libxml2 \
    libxslt1.1 \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r app && useradd -r -g app app

# Set work directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=app:app src/ ./src/
COPY --chown=app:app assets/ ./assets/
COPY --chown=app:app config/ ./config/

# Create necessary directories and set permissions
RUN mkdir -p logs temp uploads exports && \
    chown -R app:app /app && \
    chmod +x /usr/local/bin/uvicorn

# Switch to app user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["uvicorn", "src.certify_studio.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
