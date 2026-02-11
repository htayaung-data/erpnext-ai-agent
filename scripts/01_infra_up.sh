#!/usr/bin/env bash
set -euo pipefail
docker compose up -d db redis-cache redis-queue redis-socketio
docker compose ps
