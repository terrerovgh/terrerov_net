#!/bin/bash

# Create scripts directory if it doesn't exist
mkdir -p /app/scripts

# Initialize the database and create tables
sqlite3 /app/network_monitor.db << 'END_SQL'
CREATE TABLE IF NOT EXISTS network_scan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    scan_type VARCHAR(50) NOT NULL,
    target VARCHAR(100) NOT NULL,
    result TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS speed_test (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    download_speed FLOAT,
    upload_speed FLOAT,
    ping FLOAT,
    jitter FLOAT
);

CREATE TABLE IF NOT EXISTS error_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    error_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    ai_analysis TEXT
);
END_SQL

# Start the network monitoring script in the background
/app/scripts/network_monitor.sh &

# Start the Flask application
python3 /app/app.py