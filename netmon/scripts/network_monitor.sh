#!/bin/bash

# Function to log results to database
log_to_db() {
    local test_type=$1
    local result=$2
    local timestamp=$(date -u +"%Y-%m-%d %H:%M:%S")
    sqlite3 /app/network_monitor.db "INSERT INTO network_scan (timestamp, scan_type, target, result) VALUES ('$timestamp', '$test_type', 'system', '$result');"
}

# Function to log errors
log_error() {
    local error_type=$1
    local description=$2
    local timestamp=$(date -u +"%Y-%m-%d %H:%M:%S")
    sqlite3 /app/network_monitor.db "INSERT INTO error_log (timestamp, error_type, description) VALUES ('$timestamp', '$error_type', '$description');"
}

# Network monitoring script
while true; do
    echo "[$(date)] Starting network tests..."

    # Run speed test
    echo "Running speed test..."
    if speedtest_result=$(speedtest-cli --json 2>&1); then
        echo "$speedtest_result" > /tmp/speedtest_result.json
        # Extract and store speed test results in database
        download=$(echo "$speedtest_result" | jq '.download / 1000000')
        upload=$(echo "$speedtest_result" | jq '.upload / 1000000')
        ping=$(echo "$speedtest_result" | jq '.ping')
        timestamp=$(date -u +"%Y-%m-%d %H:%M:%S")
        sqlite3 /app/network_monitor.db "INSERT INTO speed_test (timestamp, download_speed, upload_speed, ping) VALUES ('$timestamp', $download, $upload, $ping);"
    else
        log_error "speed_test" "Speed test failed: $speedtest_result"
    fi

    # Test DNS resolution
    echo "Testing DNS resolution..."
    if dns_result=$(nslookup www.terrerov.com localhost 2>&1); then
        echo "DNS resolution test passed"
        log_to_db "dns_test" "success: $dns_result"
    else
        echo "WARNING: DNS resolution test failed"
        log_to_db "dns_test" "failed: $dns_result"
    fi

    # Test web access
    echo "Testing web access..."
    if web_result=$(curl -s -H "Host: www.terrerov.com" http://localhost 2>&1); then
        echo "Web access test passed"
        log_to_db "web_test" "success"
    else
        echo "WARNING: Web access test failed"
        log_to_db "web_test" "failed: $web_result"
    fi

    # Test database connection
    echo "Testing database connection..."
    if db_result=$(pg_isready -h postgres 2>&1); then
        echo "Database connection test passed"
        log_to_db "db_test" "success"
    else
        echo "WARNING: Database connection test failed"
        log_to_db "db_test" "failed: $db_result"
    fi

    # Run network scan
    echo "Running network scan..."
    if nmap_result=$(nmap -sV 172.20.0.0/16 2>&1); then
        echo "$nmap_result" > /tmp/nmap_scan.log
        log_to_db "nmap_scan" "$nmap_result"
    else
        log_error "nmap_scan" "Network scan failed: $nmap_result"
    fi

    echo "[$(date)] Network tests completed"
    # Sleep for an hour before next test
    sleep 3600
done