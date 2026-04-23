#!/usr/bin/env bash
set -e

# Default values if not set
: "${DB_HOST:=db}"
: "${DB_PORT:=5432}"
: "${DB_USER:=app}"
: "${DB_NAME:=app_db}"

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

# Wait until pg_isready succeeds
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" >/dev/null 2>&1; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done

echo "PostgreSQL is up - running migrations"
echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting app..."
exec "$@"

