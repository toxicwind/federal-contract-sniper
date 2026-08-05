#!/bin/bash
BASE="/mnt/agents/output/sam-autoscraper"
LOG="$BASE/snipes/monitor_$(date +%Y%m%d_%H%M%S).log"
cd "$BASE"
nohup python3 monitor.py > "$LOG" 2>&1 &
PID=$!
echo "$PID" > "$BASE/snipes/.pid_monitor"
echo "[MONITOR] Detached PID: $PID"
echo "[MONITOR] Log: $LOG"
echo "[MONITOR] To view: tail -f $LOG"
