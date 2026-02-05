#!/bin/sh
set -e

# Fix permissions for data and logs directories
if [ "$(id -u)" = "0" ]; then
    chown -R lumina:lumina /app/data /app/logs 2>/dev/null || true
    exec gosu lumina python main.py
fi

# Fallback: run directly
exec python main.py
