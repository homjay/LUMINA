#!/bin/sh
set -e

# Fix permissions for data and logs directories
if [ "$(id -u)" = "0" ]; then
    echo "Fixing permissions for lumina user..."
    chown -R lumina:lumina /app/data /app/logs
    echo "Starting as lumina user..."
    exec su-exec lumina python main.py
fi

# Fallback: run directly
exec python main.py
