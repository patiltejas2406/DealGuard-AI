#!/usr/bin/env bash
set -e

echo "=== DealGuard AI Database Seeder ==="
export PATH="/Users/tejas/.local/node/bin:/Users/tejas/.venv/bin:$PATH"

PYTHONPATH=backend /Users/tejas/.venv/bin/python scripts/seed.py
