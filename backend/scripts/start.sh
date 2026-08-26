#!/usr/bin/env bash
set -e

echo "=== DealGuard AI: Starting Production Backend ==="

# Execute database migrations
echo "Executing database migrations (Alembic)..."
alembic upgrade head

# Seed synthetic demo data if not already present
if [ -f "/app/scripts/seed.py" ]; then
    echo "Checking and seeding demo data..."
    python3 /app/scripts/seed.py || echo "Warning: Seed script encountered an error, continuing startup."
fi

# Launch Uvicorn server bound to dynamic Railway port
PORT="${PORT:-8000}"
echo "Starting Uvicorn server on 0.0.0.0:${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
