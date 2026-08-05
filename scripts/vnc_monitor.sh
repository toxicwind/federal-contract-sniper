#!/bin/bash
BASE="$(dirname "$0")/.."
LOG="$BASE/outputs/run/monitor_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$BASE/outputs/run"
cd "$BASE"
nohup python -m federal_sniper.cli monitor > "$LOG" 2>&1 &
PID=$!
echo "$PID" > "$BASE/outputs/run/.pid_monitor"
echo "[MONITOR] PID: $PID | Log: $LOG"
