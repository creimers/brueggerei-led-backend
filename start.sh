#!/bin/sh
# Production entry point (production.yml). Migrations and collectstatic run
# before the server starts, so `docker rollout` only reports the container
# healthy once the new code and schema are live.
set -e

uv run python /app/manage.py migrate --noinput
uv run python /app/manage.py collectstatic --noinput

exec uv run gunicorn ledmatrix.wsgi -w 2 --bind 0.0.0.0:8000 --chdir=/app \
    --access-logfile - --access-logformat "%(h)s %(t)s %(s)s %(U)s %(L)s"
