#!/usr/bin/env bash
set -e

# Waits for DATABASE_URL – works for PostgreSQL and Oracle
echo "Waiting for database..."
python scripts/wait_for_db.py

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting app..."
exec "$@"
