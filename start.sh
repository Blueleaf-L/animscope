#!/bin/bash
# Render start script

echo "=== Importing data into database ==="
cd /opt/render/project/src
python scripts/init_db.py --import-only

echo "=== Starting backend ==="
cd backend
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
