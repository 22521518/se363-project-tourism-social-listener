#!/bin/bash
set -e

# Ensure the named venv is on PATH
export VIRTUAL_ENV=${VIRTUAL_ENV:-/opt/streamlit_venv}
export PATH="$VIRTUAL_ENV/bin:$PATH"

echo "[entrypoint] using venv at $VIRTUAL_ENV"

POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
RETRIES=${WAIT_RETRIES:-30}
DELAY=${WAIT_DELAY:-1}

echo "[entrypoint] PATH=$PATH"

echo "[entrypoint] Waiting for Postgres at ${POSTGRES_HOST}:${POSTGRES_PORT} (retries=${RETRIES})"
python - <<PY
import os, socket, time, sys
host=os.getenv('POSTGRES_HOST','postgres')
port=int(os.getenv('POSTGRES_PORT','5432'))
retries=int(os.getenv('WAIT_RETRIES','30'))
delay=float(os.getenv('WAIT_DELAY','1'))
for i in range(retries):
   try:
       s=socket.create_connection((host,port), timeout=2)
       s.close()
       print('database reachable')
       sys.exit(0)
   except Exception as e:
       print(f'waiting for db... {i+1}/{retries}')
       time.sleep(delay)
print('database not reachable after retries, continuing')
sys.exit(0)
PY

echo "[entrypoint] Starting: $@"
exec "$@"
