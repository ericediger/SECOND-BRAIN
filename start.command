#!/bin/bash

# Second Brain Launcher
cd "$(dirname "$0")"

echo "Starting Second Brain..."

# Open browser after a short delay (gives server time to start)
(sleep 2 && open "http://127.0.0.1:5000") &

# Start the server
cd backend
python3 app.py
