#!/bin/bash

# Create scripts directory if it doesn't exist
mkdir -p /app/scripts

# Create the network monitoring database
sqlite3 /app/network_monitor.db ".databases"

# Start the network monitoring script in the background
/app/scripts/network_monitor.sh &

# Start the Flask application
python3 /app/app.py