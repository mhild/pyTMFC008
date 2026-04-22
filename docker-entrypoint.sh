#!/usr/bin/env bash
set -e

# Optional: wait for DB to be up
# You can add a simple pg_isready check here if needed.

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting app..."
exec "$@"