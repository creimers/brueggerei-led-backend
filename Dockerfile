# syntax=docker/dockerfile:1
FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /uvx /bin/

# curl: the container healthcheck in production.yml.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# The virtualenv lives outside /app so a bind mount of the source tree
# (docker-compose.yml) does not shadow it. UV_NO_SYNC makes `uv run ...`
# inside the container use the installed environment as is (it implies
# --frozen, so uv.lock is never touched by `uv run`); `uv lock` / `uv add`
# still work normally for dependency management.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_SYNC=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install dependencies first so this layer is cached across source changes.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=.python-version,target=.python-version \
    uv sync --frozen --no-dev

COPY . /app

EXPOSE 8000

CMD ["/app/start.sh"]
