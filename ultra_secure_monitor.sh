#!/bin/bash
# Ultra-Secure Container Runtime Monitoring
# Generated: 2025-06-19T12:13:32.677356+00:00

CONTAINER_NAME="trading-bot-ultra-secure"
LOG_FILE="/var/log/container-security-monitor.log"
ALERT_THRESHOLD=5

log_event() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

check_privilege_escalation() {
    # Check for privilege escalation attempts
    PRIV_ESCALATION=$(docker exec "$CONTAINER_NAME" ps aux | grep -c "su\|sudo\|doas" || true)
    if [ "$PRIV_ESCALATION" -gt 0 ]; then
        log_event "ALERT: Privilege escalation attempt detected in $CONTAINER_NAME"
        return 1
    fi
    return 0
}

check_capability_violations() {
    # Verify no additional capabilities were added
    CAPS=$(docker inspect "$CONTAINER_NAME" | jq -r '.[0].HostConfig.CapAdd[]' 2>/dev/null || echo "null")
    if [ "$CAPS" != "null" ] && [ "$CAPS" != "[]" ]; then
        log_event "ALERT: Unauthorized capabilities detected: $CAPS"
        return 1
    fi
    return 0
}

check_user_violations() {
    # Verify container is running as non-root
    CONTAINER_USER=$(docker exec "$CONTAINER_NAME" id -u 2>/dev/null || echo "0")
    if [ "$CONTAINER_USER" = "0" ]; then
        log_event "ALERT: Container running as root user"
        return 1
    fi
    return 0
}

check_filesystem_violations() {
    # Check for unauthorized file modifications
    MODIFIED_FILES=$(docker exec "$CONTAINER_NAME" find /app -type f -newer /app -not -path "/app/logs/*" -not -path "/app/data/*" 2>/dev/null | wc -l)
    if [ "$MODIFIED_FILES" -gt 0 ]; then
        log_event "WARNING: Unexpected file modifications detected"
    fi
}

check_network_violations() {
    # Monitor network connections
    EXTERNAL_CONNECTIONS=$(docker exec "$CONTAINER_NAME" netstat -tn 2>/dev/null | grep -c ":443\|:80" || echo "0")
    if [ "$EXTERNAL_CONNECTIONS" -gt 10 ]; then
        log_event "WARNING: High number of external connections: $EXTERNAL_CONNECTIONS"
    fi
}

check_resource_violations() {
    # Check resource usage
    MEMORY_USAGE=$(docker stats --no-stream --format "{{.MemPerc}}" "$CONTAINER_NAME" | sed 's/%//' 2>/dev/null || echo "0")
    CPU_USAGE=$(docker stats --no-stream --format "{{.CPUPerc}}" "$CONTAINER_NAME" | sed 's/%//' 2>/dev/null || echo "0")
    
    if (( $(echo "$MEMORY_USAGE > 90" | bc -l) )); then
        log_event "WARNING: High memory usage: ${MEMORY_USAGE}%"
    fi
    
    if (( $(echo "$CPU_USAGE > 90" | bc -l) )); then
        log_event "WARNING: High CPU usage: ${CPU_USAGE}%"
    fi
}

main_monitoring_loop() {
    log_event "Starting ultra-secure container monitoring for $CONTAINER_NAME"
    
    while true; do
        if docker ps | grep -q "$CONTAINER_NAME"; then
            VIOLATIONS=0
            
            check_privilege_escalation || ((VIOLATIONS++))
            check_capability_violations || ((VIOLATIONS++))
            check_user_violations || ((VIOLATIONS++))
            check_filesystem_violations
            check_network_violations
            check_resource_violations
            
            if [ "$VIOLATIONS" -ge "$ALERT_THRESHOLD" ]; then
                log_event "CRITICAL: Multiple security violations detected - Consider container restart"
                # Optional: Automatically stop container on critical violations
                # docker stop "$CONTAINER_NAME"
            fi
        else
            log_event "Container $CONTAINER_NAME is not running"
        fi
        
        sleep 30
    done
}

# Signal handlers
trap 'log_event "Monitoring stopped"; exit 0' SIGTERM SIGINT

# Start monitoring
main_monitoring_loop
