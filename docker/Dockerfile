# Multi-stage build for Linux x64: Build stage for otfcc-rs
#
# otfcc-rs (https://github.com/MaruTama/otfcc-rs) is a Rust port of caryll/otfcc
# v0.10.4 with the same CLI. It fixes the corruption of large GSUB alternate
# lookups (aalt) that caryll otfcc v0.10.4 produces (MaruTama/otfcc-rs#5).
# The Rust version matches otfcc-rs's rust-toolchain.toml; the Debian release
# (trixie) matches the production stage so the binaries' glibc is satisfied.
FROM --platform=linux/amd64 rust:1.97.1-slim-trixie AS builder

# Pinned otfcc-rs commit (bump deliberately)
ARG OTFCC_RS_REF=9f512d836d16d4c155ceb6faf2e20d624c7b204f

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Build otfccbuild / otfccdump from source (Cargo.lock is committed: --locked)
RUN git clone https://github.com/MaruTama/otfcc-rs.git /tmp/otfcc-rs && \
    cd /tmp/otfcc-rs && \
    git checkout --detach "${OTFCC_RS_REF}" && \
    rustup toolchain install && \
    cargo build --release --locked && \
    mkdir -p /otfcc-bin && \
    cp target/release/otfccbuild target/release/otfccdump /otfcc-bin/ && \
    # Verify binaries were built
    ls -la /otfcc-bin/ && \
    /otfcc-bin/otfccdump --version && \
    /otfcc-bin/otfccbuild --version

# Production stage for Linux x64
FROM --platform=linux/amd64 python:3.11-slim-trixie

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

# Copy pyproject.toml and install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy project files
COPY . .

# Set Python path for refactored module
ENV PYTHONPATH=/app/src

# Create necessary directories
RUN mkdir -p tmp/json outputs

# Set default command
CMD ["python", "-m", "refactored.cli.main", "--help"]