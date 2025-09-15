FROM python:3.12

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create a non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set environment variables for uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Create app directory and set ownership
WORKDIR /app
RUN chown -R appuser:appuser /app

# Switch to non-root user for dependency installation
USER appuser

# Copy project files for dependency resolution
COPY --chown=appuser:appuser pyproject.toml uv.lock* /app/

# Install dependencies in a separate layer for better caching
RUN uv sync --frozen --no-install-project

# Copy the rest of the application
COPY --chown=appuser:appuser . /app
