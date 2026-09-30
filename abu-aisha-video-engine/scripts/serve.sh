#!/usr/bin/env bash
# Start the review UI on http://localhost:8765
cd "$(dirname "$0")/../services/pipeline" && exec python3 -m uvicorn abu_aisha.api:app --host 127.0.0.1 --port "${PORT:-8765}"
