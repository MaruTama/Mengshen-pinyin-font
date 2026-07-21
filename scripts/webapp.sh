#!/bin/sh
# Launch the Mengshen Font Studio webapp (backend + built frontend).
set -e
cd "$(dirname "$0")/.."

if [ ! -d webapp/frontend/dist ]; then
  echo "warning: webapp/frontend/dist not found — building frontend..." >&2
  (cd webapp/frontend && npm install && npm run build)
fi

exec python -m uvicorn webapp.backend.main:app --port "${PORT:-8000}"
