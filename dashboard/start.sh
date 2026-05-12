#!/bin/bash
# dashboard/start.sh — Start all Dashboard services

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "Starting UT Orchestrator Dashboard..."

# 1. Check Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "[ERROR] Redis is not running. Start it first: redis-server"
    exit 1
fi

# 2. Start Celery worker
echo "Starting Celery worker..."
cd "$ROOT"
celery -A dashboard.backend.tasks.celery_app worker --loglevel=info &
CELERY_PID=$!

# 3. Start FastAPI
echo "Starting FastAPI backend..."
cd "$ROOT"
python -m uvicorn dashboard.backend.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# 4. Start Vite dev server
echo "Starting frontend dev server..."
cd "$ROOT/dashboard/frontend"
npm run dev &
VITE_PID=$!

echo ""
echo "Dashboard started:"
echo "  Backend API: http://localhost:8000"
echo "  Frontend:    http://localhost:5173"
echo "  API Docs:    http://localhost:8000/docs"
echo ""
echo "PIDs: Celery=$CELERY_PID  API=$API_PID  Vite=$VITE_PID"

trap "kill $CELERY_PID $API_PID $VITE_PID 2>/dev/null" EXIT
wait
