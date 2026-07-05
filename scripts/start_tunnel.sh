#!/bin/bash
# Public tunnel — keeps trying to reconnect if dropped
# Usage: bash scripts/start_tunnel.sh

PORT=8000
echo "Starting tunnel on port $PORT..."
echo "Press Ctrl+C to stop."
echo ""

while true; do
  echo "[$(date '+%H:%M:%S')] Connecting..."
  ssh -o StrictHostKeyChecking=no \
      -o ServerAliveInterval=30 \
      -o ServerAliveCountMax=3 \
      -o ExitOnForwardFailure=yes \
      -R 80:localhost:$PORT \
      localhost.run 2>&1 | while read line; do
    echo "$line"
    # Extract and highlight URL
    if echo "$line" | grep -q "https://.*\.lhr\.life"; then
      url=$(echo "$line" | grep -o 'https://[^ ]*\.lhr\.life')
      echo ""
      echo "=============================================="
      echo "  PUBLIC URL: $url"
      echo "=============================================="
      echo ""
    fi
  done
  echo "[$(date '+%H:%M:%S')] Disconnected. Reconnecting in 5s..."
  sleep 5
done
