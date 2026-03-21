#!/usr/bin/env sh
set -eu

if [ -n "${DATABASE_URL:-}" ]; then
  echo "Applying database migrations..."
  attempts=0
  until python -m alembic upgrade head; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 10 ]; then
      echo "Database migrations failed after ${attempts} attempts."
      exit 1
    fi
    echo "Database not ready yet, retrying in 3 seconds..."
    sleep 3
  done
fi

echo "Starting Buddybug backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
