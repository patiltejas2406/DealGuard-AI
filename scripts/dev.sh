#!/usr/bin/env bash
set -e

echo "=== Starting DealGuard AI Development Environment ==="

export PATH="/Users/tejas/.local/node/bin:/Users/tejas/.venv/bin:$PATH"

# Trap SIGINT to shut down background jobs
trap "kill 0" EXIT

echo "1. Starting FastAPI Backend on http://localhost:8000..."
(cd backend && PYTHONPATH=. /Users/tejas/.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) &

echo "2. Starting Next.js Frontend on http://localhost:3000..."
(cd frontend && npm run dev) &

wait
