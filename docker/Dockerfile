# Multi-stage build for Linux x64: Build stage for otfcc
FROM --platform=linux/amd64 python:3.11-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    pkg-config \
    libfreetype6-dev \
    uuid-dev \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Download and install premake5 binary for x64
RUN wget -O /tmp/premake5.tar.gz "https://github.com/premake/premake-core/releases/download/v5.0.0-beta2/premake-5.0.0-beta2-linux.tar.gz" && \
    cd /tmp && \
    tar -xzf premake5.tar.gz && \
    mv premake5 /usr/local/bin/ && \
    chmod +x /usr/local/bin/premake5 && \
    rm -f /tmp/premake5.tar.gz && \
    # Verify premake5 installation
    premake5 --version

# Build otfcc from source using the correct build process for x64
RUN git clone --depth 1 --branch v0.10.4 https://github.com/caryll/otfcc.git /tmp/otfcc && \
    cd /tmp/otfcc && \
    echo "Initializing submodules..." && \
    git submodule update --init --recursive && \
    echo "Running premake5..." && \
    premake5 gmake && \
    echo "Building with make..." && \
    cd build/gmake && \
    make config=release_x64 && \
    echo "Checking build output..." && \
    ls -la ../../bin/ && \
    ls -la ../../bin/release-x64/ && \
    mkdir -p /otfcc-bin && \
    cp ../../bin/release-x64/* /otfcc-bin/ && \
    # Verify binaries were built
    echo "Verifying binaries..." && \
    ls -la /otfcc-bin/ && \
    /otfcc-bin/otfccdump --version

# Production stage for Linux x64
FROM --platform=linux/amd64 python:3.11-slim

# Install runtime dependencies and build tools for Python packages
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    libfreetype6 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy otfcc binaries from builder stage
COPY --from=builder /otfcc-bin/* /usr/local/bin/

# Verify otfcc installation
RUN otfccdump --version && otfccbuild --version

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set Python path for refactored module
ENV PYTHONPATH=/app/src

# Create necessary directories
RUN mkdir -p tmp/json outputs

# Set default command
CMD ["python", "-m", "refactored.cli.main", "--help"]