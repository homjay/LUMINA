#!/bin/sh
set -e

# Run as the host user that owns the bind-mounted data directory.
if [ "$(id -u)" = "0" ]; then
    mkdir -p /app/data /app/logs
    TARGET_UID="$(stat -c %u /app/data 2>/dev/null || echo 1000)"
    TARGET_GID="$(stat -c %g /app/data 2>/dev/null || echo 1000)"
    exec gosu "${TARGET_UID}:${TARGET_GID}" python main.py
fi

# Already non-root
exec python main.py
