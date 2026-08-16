#!/usr/bin/env bash
set -e

echo "=== Running DealGuard AI Test Suite ==="

export PATH="/Users/tejas/.local/node/bin:/Users/tejas/.venv/bin:$PATH"

echo "1. Running Backend Unit & Security Tests (pytest)..."
PYTHONPATH=backend /Users/tejas/.venv/bin/pytest tests/backend/ -v

echo "2. Running Frontend TypeScript Typecheck & Lint..."
(cd frontend && npx tsc --noEmit)

echo "=== All Tests & Checks Passed Successfully! ==="
