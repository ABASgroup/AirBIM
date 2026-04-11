#!/bin/sh
set -e

# celery worker
echo "Starting Celery..."

echo "Running database migrations..."
alembic upgrade head

echo "Starting backend server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
