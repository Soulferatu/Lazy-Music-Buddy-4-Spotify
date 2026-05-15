#!/usr/bin/env bash
set -e

PORT="${1:-1337}"
APP_IMPORT="wacken_playlist:create_app"

# Best-effort stop of any previous dev server for this app.
if command -v pkill >/dev/null 2>&1; then
  pkill -f "flask.*${APP_IMPORT}" 2>/dev/null || true
fi

PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  PY=python
fi

echo "Starting Flask dev server on http://127.0.0.1:${PORT}"
exec "$PY" -m flask --app "$APP_IMPORT" --debug run --host 127.0.0.1 --port "$PORT"
