#!/usr/bin/env bash
set -e

echo "=== DealGuard AI: Starting Production Backend ==="

# Execute database migrations
echo "Executing database migrations (Alembic)..."
alembic upgrade head

# Launch Uvicorn server bound to dynamic Railway port
PORT="${PORT:-8000}"
echo "Starting Uvicorn server on 0.0.0.0:${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
