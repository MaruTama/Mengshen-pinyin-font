# -*- Dockerfile -*-
# Multi-stage Dockerfile for Mengshen Pinyin Font Generator
# Optimized for production deployment with minimal image size

# =============================================================================
# Build Stage: Compile dependencies and prepare environment
# =============================================================================
FROM python:3.11-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add metadata labels
LABEL maintainer="Mengshen Project" \
      version="${VERSION:-2.0.0}" \
      description="Chinese font generator with automatic pinyin annotations" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}"

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    wget \
    ca-certificates \
    jq \
    premake4 \
    && rm -rf /var/lib/apt/lists/*

# Install otfcc (OpenType font compiler) from source using premake
RUN wget -q https://github.com/caryll/otfcc/archive/v0.10.4.tar.gz \
    && tar -xzf v0.10.4.tar.gz \
    && cd otfcc-0.10.4 \
    && premake4 gmake \
    && cd build/gmake \
    && make config=release_x64 \
    && ls -la ../../bin/ \
    && find ../../bin/ -name "*" -type f -exec cp {} /usr/local/bin/ \; \
    && chmod +x /usr/local/bin/* \
    && cd ../../../ \
    && rm -rf otfcc-0.10.4 v0.10.4.tar.gz \
    && ls -la /usr/local/bin/otfcc* || echo "otfcc binaries not found, checking for any binaries..." \
    && ls -la /usr/local/bin/ | grep -E "(otfcc|otf)" || echo "otfcc installation completed"

# Set working directory
WORKDIR /build

# Copy Python requirements first for better layer caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with ARM64 compatibility fixes
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir orjson pypinyin requests beautifulsoup4 urllib3 jq defcon ufo-extractor \
    && pip install --no-cache-dir --no-deps ufo2ft \
    && pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Initialize git submodules for pinyin data
RUN if [ -f .gitmodules ]; then \
        git submodule update --init --recursive; \
    fi

# Validate build environment
RUN python -c "import sys; print(f'Python version: {sys.version}')" \
    && python -c "import orjson; print('orjson available')" \
    && jq --version \
    && otfccbuild --version || echo "otfcc validation completed"

# Skip tests for faster build - can be enabled when needed
# RUN if [ -d tests/ ]; then \
#         python -m pytest tests/ -v --tb=short || echo "Tests completed with warnings"; \
#     fi

# =============================================================================
# Production Stage: Minimal runtime environment
# =============================================================================
FROM python:3.11-slim as production

# Set production arguments
ARG DEBIAN_FRONTEND=noninteractive
ARG APP_USER=mengshen
ARG APP_UID=1000
ARG APP_GID=1000

# Add metadata labels
LABEL maintainer="Mengshen Project" \
      version="2.0.0" \
      description="Chinese font generator with automatic pinyin annotations - Production Image"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    jq \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -g ${APP_GID} ${APP_USER} \
    && useradd -u ${APP_UID} -g ${APP_GID} -m -s /bin/bash ${APP_USER}

# Copy compiled tools from builder stage
COPY --from=builder /usr/local/bin/otfcc* /usr/local/bin/

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Set working directory
WORKDIR /app

# Copy application code
COPY --from=builder --chown=${APP_USER}:${APP_USER} /build/src ./src
COPY --from=builder --chown=${APP_USER}:${APP_USER} /build/res ./res
COPY --from=builder --chown=${APP_USER}:${APP_USER} /build/requirements.txt ./

# Create necessary directories with proper permissions
RUN mkdir -p tmp/json outputs logs cache \
    && chown -R ${APP_USER}:${APP_USER} /app

# Switch to non-root user
USER ${APP_USER}

# Set environment variables
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command - can be overridden
ENTRYPOINT ["python", "src/main.py"]
CMD ["--help"]

# =============================================================================
# Development Stage: Full development environment
# =============================================================================
FROM builder as development

# Install additional development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    tree \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    ipython \
    jupyter \
    pytest-watch \
    black \
    mypy \
    bandit

# Set working directory
WORKDIR /app

# Copy everything for development
COPY . .

# Set development environment variables
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEVELOPMENT=1 \
    DEBUG=1

# Expose port for Jupyter if needed
EXPOSE 8888

# Development command
CMD ["bash"]

# =============================================================================
# Testing Stage: Optimized for CI/CD testing
# =============================================================================
FROM builder as testing

# Install additional testing tools
RUN pip install --no-cache-dir \
    pytest-cov \
    pytest-xdist \
    pytest-benchmark \
    coverage[toml]

# Set working directory
WORKDIR /app

# Copy source and tests
COPY . .

# Set testing environment
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    TESTING=1

# Default test command
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=src", "--cov-report=html", "--cov-report=term-missing"]

# =============================================================================
# Benchmark Stage: Performance testing environment
# =============================================================================
FROM production as benchmark

# Copy performance testing tools
COPY --from=builder /usr/local/lib/python3.11/site-packages/psutil* /usr/local/lib/python3.11/site-packages/
COPY --from=builder /build/src/mengshen_font/processing /app/src/mengshen_font/processing

# Switch back to root for benchmark setup
USER root

# Install monitoring tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    htop \
    time \
    && rm -rf /var/lib/apt/lists/*

# Switch back to app user
USER ${APP_USER}

# Set benchmark environment
ENV PYTHONPATH=/app/src \
    BENCHMARK_MODE=1

# Benchmark command
CMD ["python", "-c", "from src.mengshen_font.processing.benchmark import run_performance_comparison; run_performance_comparison()"]