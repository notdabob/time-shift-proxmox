#!/bin/bash
# Time-Shift Proxy Startup Script

set -e

echo "🕐 Starting Time-Shift Proxy..."

# Create log file
touch /app/logs/timeshift.log

# Start the time-shift proxy service
echo "🚀 Starting time-shift proxy on port 8090..."
python3 /app/bin/time-shift-cli.py --daemon --port 8090 &

# Keep container running
tail -f /app/logs/timeshift.log