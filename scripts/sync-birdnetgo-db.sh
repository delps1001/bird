#!/usr/bin/env bash
# Sync BirdNET-Go's SQLite database to the display Pi.
#
# Uses sqlite3's .backup command (online backup API) so the copy is
# safe even while BirdNET-Go is actively writing.
#
# Usage:
#   ./scripts/sync-birdnetgo-db.sh
#
# Cron example (every minute):
#   * * * * * /home/pi/bird-listener/scripts/sync-birdnetgo-db.sh
#
# Environment variables (all have defaults):
#   BIRDNET_DB        — source database on the BirdNET-Go Pi
#   DISPLAY_HOST      — hostname or IP of the display Pi
#   DISPLAY_DB_PATH   — destination path on the display Pi

set -euo pipefail

BIRDNET_DB="${BIRDNET_DB:-/home/dalton/birdnet-go-app/data/birdnet.db}"
DISPLAY_HOST="${DISPLAY_HOST:-192.168.1.67}"
DISPLAY_DB_PATH="${DISPLAY_DB_PATH:-/home/dalton/birdpi/bird/birdnet.db}"
STAGING="/tmp/birdnet_sync.db"

# Create a safe snapshot via SQLite's online backup API.
if ! sqlite3 "$BIRDNET_DB" ".backup '$STAGING'"; then
    echo "Error: sqlite3 backup failed" >&2
    exit 1
fi

# Transfer to the display Pi.
rsync -q "$STAGING" "${DISPLAY_HOST}:${DISPLAY_DB_PATH}"

rm -f "$STAGING"
