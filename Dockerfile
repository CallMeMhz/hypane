# AI Dashboard with Pi Agent
# Multi-stage build for smaller final image

# =============================================================================
# Stage 1: Build frontend assets
# =============================================================================
FROM node:22-alpine AS frontend-builder

WORKDIR /build

# Copy frontend dependencies
COPY frontend/package.json frontend/package-lock.json* ./frontend/
RUN cd frontend && (npm ci || npm install)

# Copy source files needed for build
COPY frontend/ ./frontend/
COPY app/templates/ ./app/templates/
COPY data/panels/ ./data/panels/

# Build frontend (outputs to /build/static)
RUN cd frontend && npm run build

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.12-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="AI Dashboard"
LABEL org.opencontainers.image.description="AI-powered personal dashboard with Pi Agent"
LABEL org.opencontainers.image.version="0.1.0"

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    DATA_DIR=/app/data \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

# =============================================================================
# System packages
# Pi Agent needs: git, common shell tools for bash/edit/read/write tools
# =============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Essential
    curl \
    wget \
    ca-certificates \
    jq \
    # Git (pi often needs this)
    git \
    # Text search (pi uses grep/ripgrep)
    ripgrep \
    # Build tools (for Python packages with C extensions)
    build-essential \
    libffi-dev \
    libssl-dev \
    # Common utilities pi might invoke
    zip \
    unzip \
    tree \
    less \
    procps \
    # For httpx/aiohttp SSL
    libssl3 \
    && rm -rf /var/lib/apt/lists/* \
    # Symlink for convenience
    && ln -sf /usr/bin/rg /usr/bin/ripgrep 2>/dev/null || true

# =============================================================================
# Python tooling
# =============================================================================
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# =============================================================================
# Node.js + Pi Agent
# =============================================================================
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Pi agent + TypeScript (for extensions)
RUN npm install -g \
    @mariozechner/pi-coding-agent \
    typescript \
    tsx

# =============================================================================
# Git config (pi often runs git commands)
# =============================================================================
RUN git config --global init.defaultBranch main \
    && git config --global --add safe.directory '*'

# =============================================================================
# Application
# =============================================================================

# Python dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Application code
COPY app/ ./app/
COPY skills/ ./skills/
COPY extensions/ ./extensions/

# Frontend assets
COPY --from=frontend-builder /build/static ./static

# Entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Data directories
RUN mkdir -p /app/data/panels /app/data/sessions /app/data/snapshots /app/data/history

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
